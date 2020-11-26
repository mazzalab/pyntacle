![Pyntacle logo](http://pyntacle.css-mendel.it/images/title_joined.png)

A Python package for network analysis based on non canonical
metrics and HPC computing

- **Compatibility**: Python 3.7
- **Contributions**: bioinformatics@css-mendel.it
- **Website**: http://pyntacle.css-mendel.it
- **Pypi**: https://pypi.org/project/pyntacle/
- **Conda**: https://anaconda.org/bfxcss/pyntacle [![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/platforms.svg)](https://anaconda.org/bfxcss/pyntacle) [![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/downloads.svg)](https://anaconda.org/bfxcss/pyntacle)
- **Docker Hub**: https://hub.docker.com/r/mazzalab/pyntacle
- **Bug report**: https://github.com/mazzalab/pyntacle/issues


## Installing using Pypi
[![PyPI version](https://badge.fury.io/py/pyntacle.svg)](https://badge.fury.io/py/pyntacle)

### [optional] Create and activate a virtualenv
#### Linux and MacOS X
```bash
python -m venv pyntacle_env
source pyntacle_env/bin/activate
```
#### Windows
```bash
python -m venv pyntacle_env
.\pyntacle_env\Scripts\activate
```
### Installation
```bash
pip install pyntacle
```


## Installing using Anaconda or Miniconda [![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/installer/conda.svg)](https://conda.anaconda.org/bfxcss)
![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/version.svg) ![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/latest_release_date.svg)

Installing Pyntacle and all its dependencies can be challenging for
inexperienced users. There are several advantages in using Anaconda to
install not only Pyntacle, but also Python and other packages: it is
cross platform (Linux, MacOS X, Windows), you do not require
administrative rights to install it (it goes in the user home
directory), it allows you to work in virtual environments, which can be
used as safe sandbox-like sub-systems that can be created, used,
exported or deleted at your will.

You can choose between the full [Anaconda](http://docs.continuum.io/anaconda/) and its lite version,
[Miniconda](http://conda.pydata.org/miniconda.html). The difference between the two is that Anaconda comes with
hundreds of packages and can be a bit heavier to install, while
Miniconda allows you to create a minimal, self-contained Python
installation, and then use the [Conda](https://conda.io/docs/) command to install additional
packages of your choice.

In any case, Conda is the package manager that the Anaconda and
Miniconda distributions are built upon. It is both cross-platform and
language agnostic (it can play a similar role to a pip and virtualenv
combination), and you need to set it up by running either the [Anaconda
installer](https://www.anaconda.com/download/) or the
[Miniconda installer](https://conda.io/miniconda.html), choosing the
Python 3.7 version.

The next step is to create a new Conda environment (if you are familiar
with virtual environments, this is analogous to a virtualenv).

#### Linux and MacOS X

Run the following commands from a terminal window:

```bash
conda create -n name_of_my_env python=3.7
```

This will create a minimal environment with only Python 3.7 installed
in it. To put your self inside this environment run:

```bash
source activate name_of_my_env
```

And finally, install the latest version of Pyntacle:

```bash
conda install -y -c bfxcss -c conda-forge pyntacle
```

#### Windows
<aside class="warning">
<b>Warning</b>: Windows users could experience some issues when installing Conda or Miniconda in folders that
whose name contains whitespaces (e.g. "%userprofile%\John Doe\Miniconda"). This is a known bug,
as reported <a href="https://github.com/ContinuumIO/anaconda-issues/issues/1029" target="_blank">here</a> and
<a href="https://groups.google.com/a/continuum.io/forum/#!topic/anaconda/zTQQ0NqqIvk" target="_blank">here</a>. If this occurs,
we recommend to create a new directory with no whitespaces (e.g. "%userprofile%\John<b style="color:red">_</b>Doe\) and install Conda in there.
</aside>


Open a windows prompt or (even better) an
[Anaconda prompt](https://chrisconlan.com/wp-content/uploads/2017/05/anaconda_prompt.png)
, and type:

```bash
conda create -y -n name_of_my_env python=3.7
```

Then, activate the newly created environment:

```bash
conda activate name_of_my_env
```

Finally, install the latest version of Pyntacle:

```bash
conda install -y -c bfxcss -c conda-forge pyntacle
```

### CUDA support (experimental)

Independently of the OS in use, if you need CUDA support, you must
also install the CUDA toolkit by downloading and installing the Toolkit from the
[_NVIDIA website_](https://developer.nvidia.com/cuda-toolkit).

**NOTE** GPU-base processing is an **experimental** feature in the current version (1.3), and is not covered by the command-line interface. This is because of weird behaviors of Numba with some hardware configurations that we were not be able to describe and circumvent so far. Although currently accessible by APIs, the GPU feature will be stable in the release 2.0, when Pyntacle will have covered the possibility to manage huge matrices for which replacing fine-grained parallelism with GPU computing would make sense.



## Release history

Changelog for current and past releases:


### 1.3.1:
Bug fixes:
- \#47 -nprocs removed in keyplayer kp-info command line
- \#48 empty result with kp-finder
- \#49 -seed argument removed in pyntacle generator
- \#50 --plot-format option removed from 1.2 onward
- \#51 seed argument removed in group degree API
- \#52 bad handling of missing output file names
- \#53 bad handling of empty set due to graph intersection

### 1.3:
Major updates:
- [algorithms] Implementation of the new Stochastic Gradient Descent (SGD) search algorithm
- [tests] Tests for SGD included
- [environment] Upgraded base Python version to 3.7
- [environment] Install igraph ver. 0.8.2 (conda-forge)

Minor updates:
- removed dependency to Cairo and the old plotter

### 1.2:
Major updates:
- [command-line] The algorithm that decides the computing configuration to be used to analyze a give graph was updated to exclude the possibility to run multi-process and multi-threaded at the same time. This is still possible by accessing directly to the APIs.
- [command-line] Renamed option from -T/--threads to -O/--nprocs to avoid clashes with other synonymous options
- [API] Removed all decorator methods that over-checked the sanity of the arguments of methods. These resulted to improve.
- [PyntacleInk] bug #28 "initial value" and "value" are swapped, solved
- [Tests] bug #25 "gr-finder bruteforce test fails", solved

Minor:
- [command-line] bug #23 "the command line option --type m-reach in kp-finder produces no output", solved
- [API] removed the *max_distance* argument from all methods
- [API] removed the seed from each methods. Postponed to later versions the implementation of clever manner of controlling randomness of number generators
- the default number of forked processes is now 1 and not equals to the total number of available processors -1
- removed *shortest_path_modifications.py* file

### 1.1:
New Graph Plotting tool: PyntacleInk
- PyntacleInk is a web-based, javascript-based visualizer based on the [sigmajs](http://sigmajs.org/) library. It is 
designed to integrate with Pyntacle command-line library and replaces the igraph-based plotter. 
- Graphical plots will be now be produced in a html file within the pyntacle results directory, containing detailed 
summarization of each Pyntacle run performed on the input file. This file is updated at each run, making graphical
expolration of results more intuitive.

### 1.0:

Major update of Pyntacle, including:
- New major feature: Group centralities. A redesign of single-node centralities that accounts for the centrality of groups have been added to Pyntacle and a new command, groupcentrality has now been added to the Pyntacle command line. Its behavior is similar to the keyplayer command. Users can compute group centrality indices for predetermined sets of nodes or perform group centrality-based searches for sets of nodes that optimize predetermined group centrality scores
- Octopus redesign
- All graphs imported from either the command line or through the `io_stream` methods now have the same id-->node name pairing, with the exceptions of pickled igraphs (binary)
- Node isolates are now removed from graphs when imported through any Pyntacle import istance
- GPU-based computation of the shortest paths using the Floyd-Warshall algorithm is now an experimental feature and is disabvled in the Pyntacle command line. Users can choose to override this behavior in the Pyntacle library by using the correct Cmode enumerator
- Added exceptions and specific behaviors to unusual group-based search calculations that caused exceptions before
- Minor bugfixes 

### 0.2:

- Added the --input-separator option to all commands.
- Added the --repeat option to pyntacle generate, so that the user can decide how many random graphs need to be created in one run.
- Bugfix in the edgelist importer, when a header is present.
- Bugfix for edgelist when node names are numbers, and now whitelines are skipped.
- Communities gracefully exits when no get_modules are found or all get_modules are filtered out by the user's custom filters.
- Major editing of the main inline help to match the documentation on the website.
- Added warnings in documentation for Windows users that have whitespaces in the Conda installation folder.
- Minor bugfixes

### 0.1.3:

- Bugfixes

### 0.1.2:

- Bugfixes

### 0.1.1:

-  The first release of Pyntacle.



## License

This work is licensed under a [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
