############
Installation
############

The easiest way for the majority of users to install pandas is to install it as part of the Anaconda distribution, a cross-platform distribution for data analysis and scientific computing. This is the recommended installation method for most users.

Instructions for installing from source on various Linux distributions and MacOs are also provided.

**********************
Python version support
**********************
Officially, Python **>= 3.5**.

*******************
Installing Pyntacle
*******************

===============================================
Installing Pyntacle using Anaconda or Miniconda
===============================================
Installing Pyntacle and all its dependencies can be challenging for inexperienced users.
There are several advantages in using Anaconda to install not only Pyntacle, but also Python and other packages: it is cross platform (Linux, MacOS X, Windows),
you do not require administrative rights to install it (it goes in the user's home directory),
it allows you to work in *virtual environments*, which can be used as safe sandbox-like sub-systems that can be created, used, exported or deleted at your will.

You can choose between the full `Anaconda <http://docs.continuum.io/anaconda/>`_ and its minified version, `Miniconda <http://conda.pydata.org/miniconda.html>`_.
The difference between the two is that Anaconda comes with hundreds of packages and can be a bit heavier to install,
while Miniconda allows you to create a minimal, self-contained Python installation, and then use the `Conda <https://conda.io/docs/>`_ command to install additional packages of your choice.

In any case, `Conda <https://conda.io/docs/>`_ is the package manager that the Anaconda and Miniconda distributions are built upon.
It is both cross-platform and language agnostic (it can play a similar role to a pip and virtualenv combination), and you need to set it up by running either the `Anaconda installer <https://www.anaconda.com/download/>`_
or the `Miniconda installer <https://conda.io/miniconda.html>`_, choosing the **Python 3.6** version.

The next step is to create a conda environment specifically for Pyntacle (if you are familiar with virtual environments, these are analogous to a virtualenv but they also allow you to specify precisely which Python version to install).
To do so, you need to download our pre-compiled **environment file**, that contain all the dependencies and their versions required to run the tool:

	* for Unix based operative system (Mac and Linux), `you can use this environment  <http://pyntacle.css-mendel.it/resources/envs/unix/pyntacle_latest.yml>`_
	* for Windows, you will need `this one <http://pyntacle.css-mendel.it/resources/envs/win/pyntacle_latest.yml>`_ 

.. note:: To date (November 2018) the environments are identical, but future releases of Pyntacle may include different dependencies for each operative system

------------------
Linux and Mac OS X
------------------

Run the following commands from a terminal window:
::

   conda env create -n pyntacle_env --file pyntacle_latest.yml

This will create a Pyntacle-ready environment running Python v.3.6. You can enter in this environment as follow:

::

  source activate name_of_my_env

And run Pyntacle freely.

-------
Windows
-------

Open a cmd terminal window or - better - an `Anaconda Prompt <https://chrisconlan.com/wp-content/uploads/2017/05/anaconda_prompt.png>`_, and type:

::

  conda env create -n pyntacle_env --file pyntacle_latest.yml

Then, we activate the newly created environment:

::

  activate name_of_my_env

.. warning:: Windows users could experience some issues when installing Conda or Miniconda in folders that have a whitespace in their name (e.g. ``C:\John Doe\Miniconda``). This is a known bug, as reported `here <https://github.com/ContinuumIO/anaconda-issues/issues/1029>`_ and `here <https://groups.google.com/a/continuum.io/forum/#!topic/anaconda/zTQQ0NqqIvk>`_. If this happens, a workaround could be to create a new user without whitespaces (e.g. ``C:\John_doe\``).
 
===============================
Installing Pyntacle from source
===============================

Installing from source is advised for advanced users only. The following instructions were written for Mac OS v.11+ and a few major Linux distros. System requirements can vary for other distros/versions.

The source code can be downloaded from our GitHub `releases <https://github.com/mazzalab/pyntacle/releases>`_ page as a .tar.gz file. Before trying to install Pyntacle, there are system requirements that need to be satisfied on each platform.

--------------
Debian, Ubuntu
--------------

As a user with admin rights, run:

::

 apt-get install -y build-essential linux-headers-$(uname -r) libgl1-mesa-glx libigraph0v5 libigraph0-dev libffi-dev libjpeg-dev libgif-dev libblas-dev liblapack-dev git python3-pip python3-tk

.. note:: **Ubuntu/Debian version <= 16.04**:
   For Ubuntu/Debian 16.04 and older, you also have to install two dependencies from the PyPi repository, by running:

   ::

    apt-get install -y build-essential linux-headers-$(uname -r) libgl1-mesa-glx libigraph0v5 libigraph0-dev libffi-dev libjpeg-dev libgif-dev libblas-dev liblapack-dev git python3-pip python3-tk


Finally, extract the Pyntacle `source tar.gz file <https://github.com/mazzalab/pyntacle/releases/latest>`_ navigate into it and run as an administrator (or add ``--user`` if you do not have admin rights and prefer to install the Pyntacle binary in ``~/.local/bin``):

::

  python3 setup.py install


--------
CentOS 7
--------

As an admin, you need to run:

::

  yum groupinstall -y development kernel-headers-`uname -r` kernel-devel-`uname -r` gcc gcc-c++ yum-utils; yum install -y https://centos7.iuscommunity.org/ius-release.rpm; yum install -y wget python36u-devel.x86_64 igraph-devel.x86_64 atlas-devel.x86_64 libffi-devel.x86_64 python36u-pip python36u-tkinter.x86_64

Finally, extract the Pyntacle `source tar.gz file <https://github.com/mazzalab/pyntacle/releases/latest>`_ navigate into it and run as an administrator (or add ``--user`` if you do not have admin rights and prefer to install the Pyntacle binary in ``~/.local/bin``):


::

  python3.6 setup.py install

--------
Mac OS X
--------

In order to compile from source, you need some of the tools that are conveniently packed in `XCode <https://itunes.apple.com/us/app/xcode/id497799835?mt=12>`_, which has to be downloaded and installed from the Mac App Store.
Once you have XCode - and you have opened at least once -, you will need to install the XCode Command Line Tools, by opening a terminal, typing:

::

  xcode-select --install

and following the prompt on screen.

Additionally, you need other dependencies to compile Pyntacle. You can easily fetch them using the package manager `Mac Ports <https://www.macports.org/install.php>`_.

Once Mac Ports is installed, getting the dependencies is easy:

::

  port install py35-setuptools py35-pandas py35-seaborn py35-colorama py35-xlsxwriter py35-igraph

Note: unfortunately, at the time of writing this guide, Mac Ports does not provide a python3.6 version of the library 'xlsxwriter'; therefore, everything must be downgraded to Python 3.5. This does not affect the performance or the results.

Finally, extract the Pyntacle `source tar.gz file <https://github.com/mazzalab/pyntacle/releases/latest>`_ navigate into it and run as an administrator:

::

  python3.5 setup.py install
  ln -s /opt/local/Library/Frameworks/Python.framework/Versions/3.5/bin/Pyntacle /opt/local/bin


============
CUDA support
============

Independently of the OS in use, if you need CUDA support, you should also install the CUDA toolkit by downloading and installing the Toolkit from the `NVIDIA website <https://developer.nvidia.com/cuda-toolkit>`_.
