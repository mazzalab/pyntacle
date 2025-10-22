#include "cuda.h"
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include "fw-kernel.h"
#include <stdio.h>
#include <float.h>

/**
 * CUDA handle error, if error occurs print message and exit program
*
* @param error: CUDA error status
*/
#define HANDLE_ERROR(error) { \
    if (error != cudaSuccess) { \
        fprintf(stderr, "%s in %s at line %d\n", \
                cudaGetErrorString(error), __FILE__, __LINE__); \
        exit(EXIT_FAILURE); \
    } \
} \

#define MAX_DISTANCE FLT_MAX / 2.0f 
// static void CudaCheck(cudaError_t error, const char *file, int line) {
//     if (error != cudaSuccess)
//     {
//         fprintf(stderr, "Error: %s:%d, ", file, line);
//         fprintf(stderr, "code: %d, reason: %s\n", error,
//                 cudaGetErrorString(error));
//         exit( EXIT_FAILURE );
//     }
// }

// #define CUDA_CHECK( err ) (CudaCheck( err, __FILE__, __LINE__ ))

/**
 * Naive CUDA kernel implementation algorithm Floyd Wharshall for APSP
 * check if path from vertex x -> y will be short using vertex u x -> u -> y
 * for all vertices in graph
 *
 * @param u: Index of vertex u
 * @param nvertex: Number of all vertex in graph
 * @param pitch: Length of row in memory
 * @param graph: Array of graph with distance between vertex on device
 * @param pred: Array of predecessors for a graph on device
 */
static __global__
void _naive_fw_kernel(const int u, size_t pitch, const int nvertex, int* const graph, int* const pred) {
    int x = blockDim.x * blockIdx.x + threadIdx.x;
    int y = blockDim.y * blockIdx.y + threadIdx.y;

    if (y < nvertex && x < nvertex) {
        int indexYX = y * pitch + x;
        int indexUX = u * pitch + x;

        int newPath = graph[y * pitch + u] + graph[indexUX];
        int oldPath = graph[indexYX];
        if (oldPath > newPath) {
            graph[indexYX] = newPath;
            pred[indexYX] = pred[indexUX];
        }
    }
}

/**
 * Naive implementation of Floyd Warshall algorithm in CUDA
 *
 * @param dataHost: Reference to unique ptr to graph data with allocated fields on host
 */
void cudaNaiveFW(float *dataHost) {
    // Choose which GPU to run on, change this on a multi-GPU system.
    HANDLE_ERROR(cudaSetDevice(0));
    int nvertex = 0;

    // Initialize the grid and block dimensions here
    dim3 dimGrid((nvertex - 1) / BLOCK_SIZE + 1, (nvertex - 1) / BLOCK_SIZE + 1, 1);
    dim3 dimBlock(BLOCK_SIZE, BLOCK_SIZE, 1);

    int *graphDevice, *predDevice;
    // size_t pitch = _cudaMoveMemoryToDevice(dataHost, &graphDevice, &predDevice);

    cudaFuncSetCacheConfig(_naive_fw_kernel, cudaFuncCachePreferL1);
    for(int vertex = 0; vertex < nvertex; ++vertex) {
        _naive_fw_kernel<<<dimGrid, dimBlock>>>(vertex, 2 / sizeof(int), nvertex, graphDevice, predDevice);
    }

    // Check for any errors launching the kernel
    HANDLE_ERROR(cudaGetLastError());
    HANDLE_ERROR(cudaDeviceSynchronize());
    // _cudaMoveMemoryToHost(graphDevice, predDevice, dataHost, pitch);
}


/**
 * Blocked CUDA kernel implementation algorithm Floyd Wharshall for APSP
 * Dependent phase 1
 *
 * @param blockId: Index of block
 * @param nvertex: Number of all vertex in graph
 * @param pitch: Length of row in memory
 * @param graph: Array of graph with distance between vertex on device
 * @param pred: Array of predecessors for a graph on device
 */
static __global__
void _blocked_fw_dependent_ph(const int blockId, size_t pitch, const int nvertex, float* const graph) {
    // declare share block ssp
    __shared__ float cacheGraph[BLOCK_SIZE][BLOCK_SIZE];

    // just one block
    const int idx = threadIdx.x;
    const int idy = threadIdx.y;

    // 2D coordinates of adj matrix
    const int vertex1 = BLOCK_SIZE * blockId + idy;
    const int vertex2 = BLOCK_SIZE * blockId + idx;

    float newPath;

    // adj matrix cell ID (pitch here is element num)
    const int cellId = vertex1 * pitch + vertex2;

    // check (needed?)
    if (vertex1 < nvertex && vertex2 < nvertex) {
        cacheGraph[idy][idx] = graph[cellId];
    } else {
        cacheGraph[idy][idx] = MAX_DISTANCE;
    }

    // Synchronize to make sure the all value are loaded in block
    __syncthreads();

    #pragma unroll
    for (int u = 0; u < BLOCK_SIZE; ++u) {

        newPath = cacheGraph[idy][u] + cacheGraph[u][idx];

        // Synchronize before calculate new value
        __syncthreads();

        if (newPath < cacheGraph[idy][idx]) {
            cacheGraph[idy][idx] = newPath;
        }

        // Synchronize to make sure that all value are current
        __syncthreads();
    }

    if (vertex1 < nvertex && vertex2 < nvertex) {
        graph[cellId] = cacheGraph[idy][idx];
    }
}

/**
 * Blocked CUDA kernel implementation algorithm Floyd Wharshall for APSP
 * Partial dependent phase 2
 *
 * @param blockId: Index of block
 * @param nvertex: Number of all vertex in graph
 * @param pitch: Length of row in memory
 * @param graph: Array of graph with distance between vertex on device
 * @param pred: Array of predecessors for a graph on device
 */
static __global__
void _blocked_fw_partial_dependent_ph(const int blockId, size_t pitch, const int nvertex, float* const graph) {
    if (blockIdx.x == blockId) return;

    const int idx = threadIdx.x;
    const int idy = threadIdx.y;

    int v1 = BLOCK_SIZE * blockId + idy;
    int v2 = BLOCK_SIZE * blockId + idx;

    __shared__ float cacheGraphBase[BLOCK_SIZE][BLOCK_SIZE];
    // __shared__ int cachePredBase[BLOCK_SIZE][BLOCK_SIZE];

    // Load base block for graph and predecessors
    int cellId = v1 * pitch + v2;

    if (v1 < nvertex && v2 < nvertex) {
        cacheGraphBase[idy][idx] = graph[cellId];
    } else {
        cacheGraphBase[idy][idx] = MAX_DISTANCE;
    }

    // Load i-aligned singly dependent blocks
    if (blockIdx.y == 0) {
        v2 = BLOCK_SIZE * blockIdx.x + idx;
    } else {
   // Load j-aligned singly dependent blocks
        v1 = BLOCK_SIZE * blockIdx.x + idy;
    }

    __shared__ float cacheGraph[BLOCK_SIZE][BLOCK_SIZE];

    // Load current block for graph and predecessors
    float currentPath;
    // int currentPred;

    cellId = v1 * pitch + v2;
    if (v1 < nvertex && v2 < nvertex) {
        currentPath = graph[cellId];
    } else {
        currentPath = MAX_DISTANCE;
    }
    cacheGraph[idy][idx] = currentPath;

    // Synchronize to make sure the all value are saved in cache
    __syncthreads();

    float newPath;
    // Compute i-aligned singly dependent blocks
    if (blockIdx.y == 0) {
        #pragma unroll
        for (int u = 0; u < BLOCK_SIZE; ++u) {
            newPath = cacheGraphBase[idy][u] + cacheGraph[u][idx];

            if (newPath < currentPath) {
                currentPath = newPath;
            }
            // Synchronize to make sure that all threads compare new value with old
            __syncthreads();

           // Update new values
            cacheGraph[idy][idx] = currentPath;

           // Synchronize to make sure that all threads update cache
            __syncthreads();
        }
    } else {
    // Compute j-aligned singly dependent blocks
        #pragma unroll
        for (int u = 0; u < BLOCK_SIZE; ++u) {
            newPath = cacheGraph[idy][u] + cacheGraphBase[u][idx];

            if (newPath < currentPath) {
                currentPath = newPath;
            }

            // Synchronize to make sure that all threads compare new value with old
            __syncthreads();

           // Update new values
            cacheGraph[idy][idx] = currentPath;

           // Synchronize to make sure that all threads update cache
            __syncthreads();
        }
    }

    if (v1 < nvertex && v2 < nvertex) {
        graph[cellId] = currentPath;
    }
}

/**
 * Blocked CUDA kernel implementation algorithm Floyd Wharshall for APSP
 * Independent phase 3
 *
 * @param blockId: Index of block
 * @param nvertex: Number of all vertex in graph
 * @param pitch: Length of row in memory
 * @param graph: Array of graph with distance between vertex on device
 * @param pred: Array of predecessors for a graph on device
 */
static __global__
void _blocked_fw_independent_ph(const int blockId, size_t pitch, const int nvertex, float* const graph) {
    if (blockIdx.x == blockId || blockIdx.y == blockId) return;

    const int idx = threadIdx.x;
    const int idy = threadIdx.y;

    //unique thread identifier
    const int v1 = blockDim.y * blockIdx.y + idy;
    const int v2 = blockDim.x * blockIdx.x + idx;

    __shared__ float cacheGraphBaseRow[BLOCK_SIZE][BLOCK_SIZE];
    __shared__ float cacheGraphBaseCol[BLOCK_SIZE][BLOCK_SIZE];
    // __shared__ int cachePredBaseRow[BLOCK_SIZE][BLOCK_SIZE];

    int v1Row = BLOCK_SIZE * blockId + idy;
    int v2Col = BLOCK_SIZE * blockId + idx;

    // Load data for block
    int cellId;
    if (v1Row < nvertex && v2 < nvertex) {
        cellId = v1Row * pitch + v2;

        cacheGraphBaseRow[idy][idx] = graph[cellId];
    }
    else {
        cacheGraphBaseRow[idy][idx] = MAX_DISTANCE;
    }

    if (v1  < nvertex && v2Col < nvertex) {
        cellId = v1 * pitch + v2Col;
        cacheGraphBaseCol[idy][idx] = graph[cellId];
    }
    else {
        cacheGraphBaseCol[idy][idx] = MAX_DISTANCE;
    }

    // Synchronize to make sure the all value are loaded in virtual block
   __syncthreads();

   float currentPath;
   float newPath;

   // Compute data for block
   if (v1  < nvertex && v2 < nvertex) {
       cellId = v1 * pitch + v2;
       currentPath = graph[cellId];

        #pragma unroll
       for (int u = 0; u < BLOCK_SIZE; ++u) {
           newPath = cacheGraphBaseCol[idy][u] + cacheGraphBaseRow[u][idx];
           if (currentPath > newPath) {
               currentPath = newPath;
           }
       }
       graph[cellId] = currentPath;
   }
}


/**
 * Blocked implementation of Floyd Warshall algorithm in CUDA
 *
 * @param data: unique ptr to graph data with allocated fields on host
 */
float* cudaBlockedFW(float* graphHost, const int nvertex) {

    printf("1D Array Input:\n");
    for (int i = 0; i < nvertex; i++) {
        printf("%f ", graphHost[i]);
    }
    printf("\n");

    HANDLE_ERROR(cudaSetDevice(0));
    
    float *graphDevice;

    size_t pitch;
    size_t width = nvertex * sizeof(float);
    size_t height = nvertex;

    HANDLE_ERROR(cudaMallocPitch(&graphDevice, &pitch, width, height));
    HANDLE_ERROR(cudaMemcpy2D(graphDevice, pitch, graphHost, width, width, height, cudaMemcpyHostToDevice));
    // printf("Allocated pitch: %zu\n", pitch);

    // number of blocks per row
    const int rowBlocks = (nvertex - 1) / BLOCK_SIZE + 1;
    printf("Allocated blocks: %d\n", rowBlocks);

    // 1D grid, single block
    dim3 gridPhase1(1 ,1, 1);
    // 2D grid ROWSx2, for rows and cols
    dim3 gridPhase2(rowBlocks, 2 , 1);
    // 2D ROWSxROWS, all the remaining blocks
    dim3 gridPhase3(rowBlocks, rowBlocks, 1);
    // 2D BLOCK 16X16
    dim3 dimBlockSize(BLOCK_SIZE, BLOCK_SIZE, 1);

    for(int blockID = 0; blockID < rowBlocks; ++blockID) {
        // Start dependent phase
        _blocked_fw_dependent_ph<<<gridPhase1, dimBlockSize>>>
                (blockID, pitch / sizeof(float), nvertex, graphDevice); //CHANGE IN FLOAT

        // Start partially dependent phase
        _blocked_fw_partial_dependent_ph<<<gridPhase2, dimBlockSize>>>
                (blockID, pitch / sizeof(float), nvertex, graphDevice); //CHANGE IN FLOAT

        // Start independent phase
        _blocked_fw_independent_ph<<<gridPhase3, dimBlockSize>>>
                (blockID, pitch / sizeof(float), nvertex, graphDevice); //CHANGE IN FLOAT
    }

    // Check for any errors launching the kernel
    HANDLE_ERROR(cudaGetLastError());
    HANDLE_ERROR(cudaDeviceSynchronize());

    HANDLE_ERROR(cudaMemcpy2D(graphHost, width, graphDevice, pitch, width, height, cudaMemcpyDeviceToHost));
    HANDLE_ERROR(cudaFree(graphDevice));

    // _cudaMoveMemoryToHost(nvertex, graphDevice, graphHost, pitch);

    printf("1D Array Output:\n");
    for (int i = 0; i < nvertex; i++) {
        printf("%f ", graphHost[i]);
    }
    printf("\n");

    return graphHost;
}