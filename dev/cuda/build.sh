
# /usr/local/cuda-12.6/bin/nvcc -lib -I ..\\common -O2 -o lib/kernel.lib cuda/kernel.cu

/usr/local/cuda-12.6/bin/nvcc -Xcompiler -fPIC -shared -o ./lib/libkernel.so ./cuda/fw-kernel.cu


python setup.py build_ext -i