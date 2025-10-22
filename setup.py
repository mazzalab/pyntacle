from setuptools import Extension, setup, find_packages
import sys
import os

# Use Cython when available, otherwise assume generated .c files are present.
try:
    from Cython.Build import cythonize
    USE_CYTHON = True
    SOURCE_EXT = ".pyx"
except Exception:
    USE_CYTHON = False
    print("Cython not found, falling back to pre-generated C files.")
    SOURCE_EXT = ".c"

# Check if we are inside a Conda environment
if 'CONDA_PREFIX' in os.environ:
    print("Conda environment detected. Using CONDA_PREFIX for library paths.")
    conda_prefix = os.environ['CONDA_PREFIX']
    
    # Construct the paths to the include and lib directories
    include_dir = os.path.join(conda_prefix, 'include')
    lib_dir = os.path.join(conda_prefix, 'lib')
else:
    # Handle the case where it's not a Conda environment (optional fallback)
    print("Not in a Conda environment. You may need to set paths manually.")
    # You could fall back to the pip-based `igraph.pkgconfig()` method here
    # or raise an error if Conda is required for your project.
    raise EnvironmentError("This build requires a Conda environment.")

if sys.platform.startswith("win"):
    openmp_arg = '/openmp'
else:
    openmp_arg = '-fopenmp'

repo_root = os.path.dirname(os.path.abspath(__file__))
# This is the path Cython needs for .pxd files
cy_path = os.path.join(repo_root, "pyntacle", "_ext") 

extensions = [

    Extension(
        "_ext.cython_metrics",
        [os.path.join(cy_path, "cython_metrics" + SOURCE_EXT)], 
        extra_compile_args=[openmp_arg],
        extra_link_args=[openmp_arg]
    ),

    Extension(
        "_ext.cython_igraph",
        [os.path.join(cy_path, "cython_igraph" + SOURCE_EXT)],
        include_dirs=[include_dir],
        library_dirs=[lib_dir],
        runtime_library_dirs=[lib_dir] if not sys.platform.startswith("win") else [],  # used at runtime on Unix
        libraries=["igraph"],            # -ligraph
        extra_compile_args=[openmp_arg],
        extra_link_args=[openmp_arg], #"-L" + lib_dir,
    ),

    Extension(
        "_ext.kp_metrics",
        [os.path.join(cy_path, "kp_metrics" + SOURCE_EXT)],
    ),
    Extension(
        "_ext.group_metrics",
        [os.path.join(cy_path, "group_metrics" + SOURCE_EXT)],
    ),
    Extension(
        "_ext.utils",
        [os.path.join(cy_path, "utils" + SOURCE_EXT)], 
    ),

    # Add more Extension objects here for other modules
]

# Cythonize if available, else expect .c files in src/
if USE_CYTHON:
    extensions = cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
        include_path=[cy_path]  
    )
else:
    # When not using Cython, ensure the .c files actually exist:
    missing = [e.sources[0] for e in extensions if not os.path.exists(e.sources[0])]
    if missing:
        raise RuntimeError("Cython not installed and generated C files missing: " + ", ".join(missing))


setup(
    name="pyntacle",
    version="0.1.0",
    package_dir={'': 'pyntacle'},
    packages=find_packages(where='pyntacle'),    
    ext_modules=extensions,
)
