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

# igraph's C library is taken from the active Conda environment
if 'CONDA_PREFIX' in os.environ:
    print("Conda environment detected. Using CONDA_PREFIX for library paths.")
    conda_prefix = os.environ['CONDA_PREFIX']
    
    include_dir = os.path.join(conda_prefix, 'include')
    lib_dir = os.path.join(conda_prefix, 'lib')
else:
    print("Not in a Conda environment. You may need to set paths manually.")
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
        extra_link_args=[openmp_arg],
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
]

# Cythonize if available, else expect the generated .c files
if USE_CYTHON:
    extensions = cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
        include_path=[cy_path]  
    )
else:
    missing = [e.sources[0] for e in extensions if not os.path.exists(e.sources[0])]
    if missing:
        raise RuntimeError("Cython not installed and generated C files missing: " + ", ".join(missing))


setup(
    name="pyntacle",
    version="0.1.0",
    package_dir={'': 'pyntacle'},
    packages=find_packages(where='pyntacle'),    
    ext_modules=extensions,
    extras_require={"omics": ["scikit-learn", "statsmodels"], "omics-annotation": ["mygene"]},
)
