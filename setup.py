import os
import re
import sys
import tempfile

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

# Use Cython when available, otherwise build from the generated .c files.
try:
    from Cython.Build import cythonize
    USE_CYTHON = True
    SOURCE_EXT = ".pyx"
except ImportError:
    USE_CYTHON = False
    SOURCE_EXT = ".c"

EXT_DIR = os.path.join("pyntacle", "_ext")

# Only cython_metrics runs parallel loops (-np).
OPENMP_EXTENSIONS = {"pyntacle._ext.cython_metrics"}

OPENMP_TEST = """
#include <omp.h>
int main(void) { return omp_get_max_threads() > 0 ? 0 : 1; }
"""


def openmp_candidates(compiler_type):
    """(compile flags, link flags) to try, in order, for this compiler."""
    if compiler_type == "msvc":
        return [(["/openmp"], [])]
    candidates = [(["-fopenmp"], ["-fopenmp"])]
    if sys.platform == "darwin":
        # Apple clang has no -fopenmp driver flag: it needs libomp, from
        # conda (llvm-openmp) or Homebrew (brew install libomp)
        for prefix in (os.environ.get("CONDA_PREFIX"), "/opt/homebrew/opt/libomp",
                       "/usr/local/opt/libomp"):
            if prefix and os.path.exists(os.path.join(prefix, "include", "omp.h")):
                lib = os.path.join(prefix, "lib")
                candidates.append((["-Xpreprocessor", "-fopenmp", "-I" + os.path.join(prefix, "include")],
                                   ["-L" + lib, "-Wl,-rpath," + lib, "-lomp"]))
    return candidates


class BuildExt(build_ext):
    """Compiles cython_metrics with the first OpenMP flags that build and link a
    test program, or without OpenMP (one thread) when none does."""

    def build_extensions(self):
        flags = None
        if os.environ.get("PYNTACLE_NO_OPENMP") != "1":
            for cflags, ldflags in openmp_candidates(self.compiler.compiler_type):
                if self._links(cflags, ldflags):
                    flags = (cflags, ldflags)
                    break
        if flags is None:
            print("WARNING: no OpenMP found for this compiler; Pyntacle is built "
                  "without it and its compiled kernels will run on one thread (-np is ignored).")
        else:
            print("OpenMP: compile with " + " ".join(flags[0]) + ", link with " + " ".join(flags[1]))
        for e in self.extensions:
            if flags is not None and e.name in OPENMP_EXTENSIONS:
                e.extra_compile_args = e.extra_compile_args + flags[0]
                e.extra_link_args = e.extra_link_args + flags[1]
        super().build_extensions()

    def _links(self, cflags, ldflags):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "openmp_test.c")
            with open(src, "w") as fh:
                fh.write(OPENMP_TEST)
            try:
                objects = self.compiler.compile([src], output_dir=tmp, extra_postargs=cflags)
                self.compiler.link_executable(objects, os.path.join(tmp, "openmp_test"),
                                              extra_postargs=ldflags)
            except Exception:
                return False
        return True


def ext(name):
    return Extension("pyntacle._ext." + name, [os.path.join(EXT_DIR, name + SOURCE_EXT)])


extensions = [ext(name) for name in ("cython_metrics", "kp_metrics", "group_metrics", "utils")]

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

# the version is set once, in pyntacle/__init__.py
with open(os.path.join("pyntacle", "__init__.py"), encoding="utf-8") as fh:
    VERSION = re.search(r'^__version__ = "([^"]+)"', fh.read(), re.M).group(1)

setup(
    name="pyntacle",
    version=VERSION,
    description="Network analysis: key players, group centrality, percolation and omics networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Manuel Mangoni, Alessandro Napoli, Michele Pieroni, Tommaso Mazza",
    maintainer="Tommaso Mazza",
    url="https://github.com/mazzalab/pyntacle",
    project_urls={"Documentation": "https://pyntacle.readthedocs.io"},
    license="GPL-3.0-only",
    python_requires=">=3.10",
    packages=find_packages(include=["pyntacle", "pyntacle.*"]),
    ext_modules=extensions,
    cmdclass={"build_ext": BuildExt},
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
        "Operating System :: MacOS",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
