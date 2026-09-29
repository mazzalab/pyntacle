import os
import sys

from setuptools import Extension, find_packages, setup

# Use Cython when available, otherwise build from the generated .c files.
try:
    from Cython.Build import cythonize
    USE_CYTHON = True
    SOURCE_EXT = ".pyx"
except ImportError:
    USE_CYTHON = False
    SOURCE_EXT = ".c"

# The extensions link igraph's C library from the active Conda environment
# (see environment.yml).
if "CONDA_PREFIX" not in os.environ:
    raise EnvironmentError(
        "Pyntacle builds against igraph's C library from a Conda environment: "
        "create it with `conda env create -f environment.yml`, activate it and "
        "run `pip install .` again.")
conda_prefix = os.environ["CONDA_PREFIX"]
if sys.platform.startswith("win"):
    include_dir = os.path.join(conda_prefix, "Library", "include")
    lib_dir = os.path.join(conda_prefix, "Library", "lib")
    openmp_arg = "/openmp"
else:
    include_dir = os.path.join(conda_prefix, "include")
    lib_dir = os.path.join(conda_prefix, "lib")
    openmp_arg = "-fopenmp"

EXT_DIR = os.path.join("pyntacle", "_ext")


def ext(name, **kwargs):
    return Extension("pyntacle._ext." + name, [os.path.join(EXT_DIR, name + SOURCE_EXT)], **kwargs)


openmp = dict(extra_compile_args=[openmp_arg], extra_link_args=[openmp_arg])
extensions = [
    ext("cython_metrics", **openmp),
    ext("cython_igraph",
        include_dirs=[include_dir],
        library_dirs=[lib_dir],
        runtime_library_dirs=[] if sys.platform.startswith("win") else [lib_dir],
        libraries=["igraph"],
        **openmp),
    ext("kp_metrics"),
    ext("group_metrics"),
    ext("utils"),
]

if USE_CYTHON:
    extensions = cythonize(extensions, compiler_directives={"language_level": "3"},
                           include_path=[EXT_DIR])
else:
    missing = [e.sources[0] for e in extensions if not os.path.exists(e.sources[0])]
    if missing:
        raise RuntimeError("Cython is not installed and the generated C files are missing: "
                           + ", ".join(missing))

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyntacle",
    version="0.1.0",
    description="Network analysis: key players, group centrality, percolation and omics networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mazzalab/pyntacle",
    license="GPL-3.0-only",
    python_requires=">=3.10",
    packages=find_packages(include=["pyntacle", "pyntacle.*"]),
    ext_modules=extensions,
    install_requires=[
        "numpy>=1.23",
        "pandas>=1.5",
        "igraph>=0.10",
        "matplotlib>=3.5",
        "pycairo>=1.20",
        "pygraphviz>=1.9",
        "plotly>=5.0",
        "colorama>=0.4",
    ],
    extras_require={
        "omics": ["scipy>=1.9", "scikit-learn>=1.1", "statsmodels>=0.13"],
        "omics-annotation": ["mygene"],
    },
    entry_points={"console_scripts": ["pyntacle = pyntacle.main:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
