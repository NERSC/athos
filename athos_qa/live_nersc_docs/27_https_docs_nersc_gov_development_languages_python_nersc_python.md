# Source: https://docs.nersc.gov/development/languages/python/nersc-python/

## How to use Python on NERSC systems ¶


## Python environment options ¶

There are 4 options for using and configuring your Python environment at NERSC. We provide a brief overview here and will explain each option in greater detail below.
Use the NERSC python module
Create a custom conda environment
Use a Shifter container (best practice for 10+ nodes)
Install your own Python
If you intend to run at large scale (10+ nodes), Shifter is the best option. You can also install your Python installation or conda environment on our faster /global/common/software filesystem. We provide more discussion about how to achieve good performance by choosing the right filesystems .
/global/common/software

## Option 1: NERSC python module ¶

The NERSC python module provides a python environment with several commonly used python packages pre-installed. To use the NERSC python module, run the following command:
module load python
module load python
This is a useful option for common tasks that require python but also the least flexible. If you require a package that is not in NERSC python environment, this option will not work for you.
Who should use Option 1?
Option 1 is best for users who want to get started quickly and who do not require special libraries or custom packages.

## Option 2: Custom conda environment ¶

NERSC provides a minimal conda installation that you can use to build your own custom conda environment. First, load the conda module:
module load conda
module load conda
You will now be able to use conda commands to create and manage custom conda environments. For example, to create an environment named "myenv" with a recent Python and the numpy package, run:
conda
conda create --name myenv python = 3 .11 numpy
conda create --name myenv python = 3 .11 numpy
By default, conda will install software to your home directory. We recommend installing conda environments to your project directory on /global/common/software if they will be used to run parallel applications at NERSC.
/global/common/software
After creating an environment, you need to activate the environment in order to use it:
conda activate myenv
conda activate myenv
Now your custom conda environment is active and you can use it to accomplish your task.
For more information about using conda, see the overview below or refer to the official conda documentation .
Who should use Option 2?
This is our most popular option. It is good for anyone who would like to use packages that not avaible in the Python module.

## Option 3: Install/Use Python inside a Shifter container ¶

We strongly suggest this option for any user who needs to run Python on 10+ nodes. This will result in better performance for your own application, make you less vulnerable to filesystem slowdowns caused by other users, and of course prevent causing filesystem slowdowns for other users. Please see our Python in Shifter documentation and examples.
Who should use Option 3?
Option 3 is suitable for users willing to build their own software stack inside of a container. mpi4py works best at scale in Shifter .

## Option 4: Install your own Python ¶

You don't have to use any of the Python options we described above- you are free to install your own Python via Miniconda, Anaconda, Intel Python, or a custom collaboration install to have complete control over your stack.
Collaborations, projects, or experiments may wish to install a shareable, managed Python stack to /global/common/software independent of the NERSC modules. You are welcome to use the Anaconda installer script for this purpose. In fact you may want to consider the more "stripped-down" Miniconda installer as a starting point. That option allows you to start with only the bare essentials and build up. Be sure to select Linux version in either case. For instance:
/global/common/software
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b \ -p /global/common/software/myproject/env [ installation messages ] source /global/common/software/myproject/env/bin/activate
conda install <only-what-my-project-needs>
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b \ -p /global/common/software/myproject/env [ installation messages ] source /global/common/software/myproject/env/bin/activate
conda install <only-what-my-project-needs>
You can customize the path with the -p argument. The installation above would go to $HOME/miniconda3 without it. You should also consider the PYTHONSTARTUP environment variable which you may wish to unset altogether. It is mainly relevant to the system Python we advise against using.
-p
$HOME/miniconda3
PYTHONSTARTUP
Who should use Option 4?
Option 4 is suitable for individuals or collaborations who would like to install, maintain, and control their own Python stack. Users who choose Option 4 should not combine their custom Python installations with our NERSC Python modules.

## Using conda, mamba, and pip to install packages and manage environments ¶


## Overview of conda ¶

Anaconda provides a conda cheat sheet you may find helpful.
To find availble packages, you can use the conda search tool. To install packages, you can use the conda install command.
conda search
conda install
conda search numpy
conda install numpy
conda search numpy
conda install numpy
Conda has several default channels that will be used first for package installation. If you want to use another channel beyond the defaults channel, you can, but we suggest that you select your channel carefully. We also suggest that you choose channels as you need them rather than permanently adding them to your conda config or .condarc file. For example, conda install numpy --channel conda-forge is better than conda config --add channels conda-forge .
conda config
.condarc
conda install numpy --channel conda-forge
conda config --add channels conda-forge
The installed package and/or its dependencies may vary depending on the the conda channel it is installed from. For example, installing numpy from the defaults channel will install MKL BLAS backend while installing numpy from the conda-forge channel will install an OpenBLAS backend.
numpy
defaults
numpy
conda-forge
Installing numpy from conda-forge with MKL
To install numpy from conda-forge with an MKL BLAS backend, use: conda install -c conda-forge numpy "libblas=*=*mkl" For more information about choosing a BLAS backend in conda-forge , see this section of the conda-forge channel knowledge base.
numpy
conda-forge
conda install -c conda-forge numpy "libblas=*=*mkl"
conda install -c conda-forge numpy "libblas=*=*mkl"
conda-forge
conda-forge
In some cases, you may need to specify more than one conda channel to satisfy a packages dependency requirements. It may be important to consider the order in which channels are specified in cases where a package or its dependency are provided by more than one of the channels. For more details, see the Managing Channels page of the conda documentation.
If you find conda is slow, try mamba instead
conda
mamba
The conda tool can sometimes be very slow when it's resolving packages in large and complex environments. You can try mamba instead of conda by simply replacing conda with mamba .
conda
conda
conda
mamba

## Installing libraries via pip ¶

You can use pip to install packages Python packages at NERSC but users should be aware of several features of pip behavior that can cause problems. Anaconda provides some Best practices for using pip with conda . Our suggested use of pip is inside a conda environment. This makes it very easy to know exactly where packages are installed and also easy to clean them up completely when you are done. We suggest the following:
pip
pip
pip
module load conda
conda activate myenv
pip install numpy
module load conda
conda activate myenv
pip install numpy
The following pip install options are useful for situations where you need to build a package from source on NERSC systems (such as mpi4py or parallel h5py ).
pip install
-v : verbose output, useful for debugging and confirming expected behavior.
-v
--force-reinstall : forces a reinstall/rebuild in case the package is already installed.
--force-reinstall
--no-cache-dir : don't use the local package cache, we want a fresh download of the source code.
--no-cache-dir
--no-binary : we want to build the package from source so don't use existing binaries.
--no-binary
--no-build-isolation : build the package using dependencies from the current environment.
--no-build-isolation
--no-deps : don't install dependent packages, we want to use the ones in the current environment.
--no-deps
See the pip documentation for more information.
pip search path can find incompatible packages
When you pip install <package> , the pip tool with traverse its search path and may discover an old version of is already installed. However, this package may be incompatible with your current setup. It may have even been built on a different sytem. To be safe, it's best to pip install with the --force-reinstall and --no-cache-dir options to ensure a new and compatible package will be installed.
pip install <package>
--force-reinstall
--no-cache-dir

## Moving your conda setup to /global/common/software ¶

/global/common/software
For better performance or if you plan to run your application at scale, we recommend installing your custom environment in your project's directory on /global/common/software :
/global/common/software
module load conda
conda create --prefix /global/common/software/myproject/myenv python = 3 .8
conda activate /global/common/software/myproject/myenv
conda install numpy scipy astropy
module load conda
conda create --prefix /global/common/software/myproject/myenv python = 3 .8
conda activate /global/common/software/myproject/myenv
conda install numpy scipy astropy
You can also change your default conda location to /global/common/software . An easy way to do this is to change the settings in your $HOME/.condarc file
/global/common/software
$HOME/.condarc
envs_dirs: - /global/common/software/<your project>/conda

pkgs_dirs: - /global/common/software/<your project>/conda

channels: - defaults
envs_dirs: - /global/common/software/<your project>/conda

pkgs_dirs: - /global/common/software/<your project>/conda

channels: - defaults
This will place all of your environments in this directory by default, and you won't have to worry about specifying the full prefix to your environment when installing it or activating it.
We are aware the project directory quotas on /global/common/software are small. Please open a ticket at help.nersc.gov if you need more space.
/global/common/software
help.nersc.gov