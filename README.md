# Pyntacle [![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/downloads.svg)](https://anaconda.org/bfxcss/pyntacle)

A python command-line tool for network analysis based on non canonical
metrics and HPC computing.

- **Compatibility**: Python 3.6+
- **Contributions**: bioinformatics@css-mendel.it
- **Website**: http://pyntacle.css-mendel.it
- **Bug report**: https://github.com/mazzalab/pyntacle/issues
- [![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/platforms.svg)](https://anaconda.org/bfxcss/pyntacle)

## Installation

The easiest way to install Pyntacle is to download it from [**Anaconda**](http://docs.continuum.io/anaconda/), 
a cross-platform distribution for data analysis and scientific computing. This is the
recommended installation method for most users.

Instructions for installing from source on various Linux distributions
and MacOS X are also provided.


### Installing Pyntacle using Anaconda or Miniconda
[![Anaconda-Server Badge](https://anaconda.org/bfxcss/pyntacle/badges/installer/conda.svg)](https://conda.anaconda.org/bfxcss)

Installing Pyntacle and all its dependencies can be challenging for
inexperienced users. There are several advantages in using Anaconda to
install not only Pyntacle, but also Python and other packages: it is
cross platform (Linux, MacOS X, Windows), you do not require
administrative rights to install it (it goes in the user home
directory), it allows you to work in virtual environments, which can be
used as safe sandbox-like sub-systems that can be created, used,
exported or deleted at your will.

You can choose between the full [Anaconda](http://docs.continuum.io/anaconda/) and its lite version,
[Miniconda](http://conda.pydata.org/miniconda.html) . The difference between the two is that Anaconda comes with
hundreds of packages and can be a bit heavier to install, while
Miniconda allows you to create a minimal, self-contained Python
installation, and then use the [Conda](https://conda.io/docs/) command to install additional
packages of your choice.

In any case, Conda is the package manager that the Anaconda and
Miniconda distributions are built upon. It is both cross-platform and
language agnostic (it can play a similar role to a pip and virtualenv
combination), and you need to set it up by running either the [Anaconda
installer](https://www.anaconda.com/download/) or the
[Miniconda installer](https://conda.io/miniconda.html) , choosing the
++Python 3.X++ version.

The next step is to create a new Conda environment (if you are familiar
with virtual environments, these are analogous to a virtualenv but they
also allow you to specify precisely which Python version to install).

#### Linux and MacOS X

Run the following commands from a terminal window:

```bash
conda create -n name_of_my_env python=3.6
```

This will create a minimal environment with only Python v.3.6 installed
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
conda create -y -n name_of_my_env python=3.6
```

Then, activate the newly created environment:

```bash
activate name_of_my_env
```

Finally, install the latest version of Pyntacle:

```bash
conda install -y -c bfxcss -c conda-forge pyntacle
```

### Installing Pyntacle from source
Installing from source is advised for advanced users only. The following
instructions were written for Mac OS v.11+ and a few major Linux
distros. System requirements can vary for other distros/versions.

The source code can be downloaded from our GitHub
[releases](https://github.com/mazzalab/pyntacle/releases) page as a
.tar.gz file. Before trying to install Pyntacle, there are system
requirements that need to be satisfied on each platform.


**NOTE** Starting from this version (1.1), we introduced a new JavaScript-based graph visualizer, PyntacleInk. Installation
of cairo and the pycairo python bindings is hence not required. We however recommend installing cairo if you seek to 
perform plotting with igraph library (visit the [pycairo page](https://cairographics.org/download/) for operative-system
specific instructions.)

#### Debian, Ubuntu

As a user with admin rights, run:

```bash
apt-get install -y build-essential linux-headers-$(uname -r) libgl1-mesa-glx libigraph0v5 libigraph0-dev libffi-dev libjpeg-dev libgif-dev libblas-dev liblapack-dev git python3-pip python3-tk
```

> #### Ubuntu/Debian version <= 16.04
> For Ubuntu/Debian 16.04 and older, you also have to install two dependencies from the PyPi repository, by running:
>```
>pip3 install numpy
>pip3 install llvmlite
>```
>
>Then, the numba package needs to be installed manually by cloning the developer's Git repository:
>
>```bash
>git clone git://github.com/numba/numba.git ; cd numba; python3 setup.py install; cd ..; rm -rf numba
>```


Finally, extract the pyntacle [_source tar.gz_](https://github.com/mazzalab/pyntacle/releases) file navigate into it and run as an administrator (or add ```--user``` if you do not have admin rights and prefer to install the pyntacle binary in ```~/.local/bin```):

```bash
python3 setup.py install
```

#### CentOS7

As an admin, you need to run:

```bash
yum groupinstall -y development kernel-headers-`uname -r` kernel-devel-`uname -r` gcc gcc-c++ yum-utils; yum install -y https://centos7.iuscommunity.org/ius-release.rpm; yum install -y wget python36u-devel.x86_64 igraph-devel.x86_64 atlas-devel.x86_64 libffi-devel.x86_64 python36u-pip python36u-tkinter.x86_64
```

Finally, extract the Pyntacle [_source tar.gz_](https://github.com/mazzalab/pyntacle/releases) file, navigate into the
extracted folder and run as an administrator (or add ```--user``` if you do not have admin rights and prefer to install the Pyntacle binary in ```~/.local/bin```):

```bash
python3.6 setup.py install
```

#### MacOS X

In order to compile from source, you need some of the tools that are
conveniently packed in
[XCode](https://itunes.apple.com/us/app/xcode/id497799835?mt=12), which
has to be downloaded and installed from the Mac App Store. Once you have
XCode - and you have opened at least once -, you will need to install
the XCode Command Line Tools, by opening a terminal, typing:

```bash
xcode-select --install
```
and following the prompt on screen.

Additionally, you need other dependencies to compile Pyntacle. You can
easily fetch them using the package manager
[Mac Ports](https://www.macports.org/install.php) .

Once Mac Ports is installed, getting the dependencies is easy:

```bash
port install py36-setuptools py36-pandas py36-seaborn py36-colorama py36-xlsxwriter py36-igraph py36-numba py36-psutil
```

Finally, extract the Pyntacle [_source tar.gz_](https://github.com/mazzalab/pyntacle/releases) file, navigate into it and run:

```bash
python3.6 setup.py install --user
```

For your convenience, you can make the newly installed binary available system-wide (requires administrative rights):

```
ln -s /Users/$USER/Library/Python/3.6/bin/pyntacle /opt/local/bin
```

### CUDA support (experimental)

Independently of the OS in use, if you need CUDA support, you must
also install the CUDA toolkit by downloading and installing the Toolkit from the
[_NVIDIA website_](https://developer.nvidia.com/cuda-toolkit).

## Release history

Changelog for current and past releases:


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

This work is licensed under a <a rel="license"
href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License v3.0</a>.

<a rel="license"
href="https://www.gnu.org/licenses/gpl-3.0.en.html"><img
alt="GNU General Public License v3.0" style="border-width:0"
src="https://en.wikipedia.org/wiki/GNU_General_Public_License#/media/File:GPLv3_Logo.svg" /></a><br
/>



