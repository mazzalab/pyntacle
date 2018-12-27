# Pyntacle

A python command line tool for network analysis based on non canonical
metrics and HPC computing.

- **Compatibility**: Python 3.5+
- **Contributions**: bioinformatics@css-mendel.it
- **Website**: http://pyntacle.css-mendel.it
- **Bug report**: https://github.com/mazzalab/pyntacle/issues

## Installation

The easiest way for the majority of users to install Pyntacle is to
install it as part of the **Anaconda** distribution, a cross-platform
distribution for data analysis and scientific computing. This is the
recommended installation method for most users.

Instructions for installing from source on various Linux distributions
and MacOS X are also provided.


### Installing Pyntacle using Anaconda or Miniconda

Installing Pyntacle and all its dependencies can be challenging for
inexperienced users. There are several advantages in using Anaconda to
install not only Pyntacle, but also Python and other packages: it is
cross platform (Linux, MacOS X, Windows), you do not require
administrative rights to install it (it goes in the user’s home
directory), it allows you to work in virtual environments, which can be
used as safe sandbox-like sub-systems that can be created, used,
exported or deleted at your will.

You can choose between the full [Anaconda](http://docs.continuum.io/anaconda/) and its minified version,
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
++Python 3.6++ version.

The next step is to create a new conda environment (if you are familiar
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
<b>Warning</b>: Windows users could experience some issues when installing
Conda or Miniconda in folders that have a whitespace in their name
(e.g. "C:\John Appleseed\Miniconda"). This is a known bug, as reported
here and here. If this happens, a workaround could be to create a new
user without whitespaces (e.g. "C:\John<b>_</b>Appleseed\).
</aside>


Open a cmd terminal window or - better - an
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

#### Debian, Ubuntu

As a user with admin rights, run:

```bash
apt-get install -y build-essential linux-headers-$(uname -r) libgl1-mesa-glx libigraph0v5 libigraph0-dev libcairo2-dev libffi-dev libjpeg-dev libgif-dev libblas-dev liblapack-dev git python3-pip python3-tk
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
yum groupinstall -y development kernel-headers-`uname -r` kernel-devel-`uname -r` gcc gcc-c++ yum-utils; yum install -y https://centos7.iuscommunity.org/ius-release.rpm; yum install -y wget python36u-devel.x86_64 igraph-devel.x86_64 cairo-devel.x86_64 atlas-devel.x86_64 libffi-devel.x86_64 python36u-pip python36u-tkinter.x86_64
wget https://github.com/pygobject/pycairo/releases/download/v1.14.1/pycairo-1.14.1.tar.gz ; tar -xf pycairo-1.14.1.tar.gz; cd pycairo-1.14.1; python3.6 setup.py build ; sudo python3.6 setup.py install; cd ..; rm -rf pycairo-1.14.1*
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
port install py36-cairo py36-setuptools py36-pandas py36-seaborn py36-colorama py36-xlsxwriter py36-igraph py36-numba py36-psutil
```

Finally, extract the Pyntacle [_source tar.gz_](https://github.com/mazzalab/pyntacle/releases) file, navigate into it and run:

```bash
python3.6 setup.py install --user
```

For your convenience, you can make the newly installed binary available system-wide (requires administrative rights):

```
ln -s /Users/$USER/Library/Python/3.6/bin/pyntacle /opt/local/bin
```

### CUDA support

Independently of the OS in use, if you need CUDA support, you should
also install the CUDA toolkit by downloading and installing the Toolkit from the
[_NVIDIA website_](https://developer.nvidia.com/cuda-toolkit).

## Release history

Changelog for current and past releases:

### 0.2:

- Added the --input-separator option to all commands.
- Added the --repeat option to pyntacle generate, so that the user can decide how many random graphs need to be created in one run.
- Bugfix in the edgelist importer, when a header is present.
- Bugfix for edgelist when node names are numbers, and now whitelines are skipped.
- Communities gracefully exits when no modules are found or all modules are filtered out by the user's custom filters.
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
href="http://creativecommons.org/licenses/by-nc-nd/4.0/">Creative
Commons Attribution-NonCommercial-NoDerivatives 4.0 International
License</a>.

<a rel="license"
href="http://creativecommons.org/licenses/by-nc-nd/4.0/"><img
alt="Creative Commons License" style="border-width:0"
src="https://i.creativecommons.org/l/by-nc-nd/4.0/88x31.png" /></a><br
/>


