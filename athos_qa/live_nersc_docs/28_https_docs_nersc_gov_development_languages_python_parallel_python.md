# Source: https://docs.nersc.gov/development/languages/python/parallel-python/

## How to use parallelism in Python ¶

Since you are running at NERSC you may be interested in parallelizing your Python code and/or its I/O. This is a detailed topic but we will provide a short overview of several options.
If you intend to to run your code at scale, please see our discussion on scaling Python that provides a brief overview of best file system practices for scaling up.

## Multiprocessing ¶

Python's standard library provides a multiprocessing package that supports spawning of processes. Multiprocessing can be used to achieve some level of parallelism within a single compute node. Currently it cannot be used to achieve parallelism across compute nodes.

## Launching programs ¶

Since multiprocessing jobs are single node only, in general you will not need Slurm srun . You can run your jobs on a compute node via
srun
python my_multiprocessing_script.py
python my_multiprocessing_script.py
When using Slurm srun , use --cpu-bind=none for multiprocessing
srun
--cpu-bind=none
If you do want or need to use Slurm srun , make sure you set
srun
srun -n 1 --cpu-bind = none python my_multiprocessing_script.py
srun -n 1 --cpu-bind = none python my_multiprocessing_script.py
to ensure that your single task is able to use all cores on the node. Note that this is different than the advice you may get from our NERSC jobscript generator as this configuration is somewhat unusual. Using --cpu-bind=cores will bind your single task to a single physical core instead of allowing your multiprocessing code to use all resources on the node.
--cpu-bind=cores

## Choosing the number of processes to use ¶

The optimal number of processes to use may vary depending on the application and the number of cpu resources to the application at run time. By default, multiprocessing.Pool will start os.cpu_count() number of processes. The number returned by os.cpu_count() is the total number of cpus ("hardware threads"). This may oversuscribe the cpu resources available to the application at run time and hinder performance.
multiprocessing.Pool
os.cpu_count()
os.cpu_count()
This is especially an issue when the number of cpus available to an application is restricted. For example, a sconjob running in the cron qos on perlmutter will be allocated a single physical core but os.cpu_count() will report the total number of logical cores on the node.
cron
os.cpu_count()
The following script demonstrates how to get a count of the total and available number of threads and cores in a Python application.
import multiprocessing as mp import os import psutil nthreads = psutil . cpu_count ( logical = True ) ncores = psutil . cpu_count ( logical = False ) nthreads_per_core = nthreads // ncores nthreads_available = len ( os . sched_getaffinity ( 0 )) ncores_available = nthreads_available // nthreads_per_core assert nthreads == os . cpu_count () assert nthreads == mp . cpu_count () print ( f ' { nthreads =} ' ) print ( f ' { ncores =} ' ) print ( f ' { nthreads_per_core =} ' ) print ( f ' { nthreads_available =} ' ) print ( f ' { ncores_available =} ' )
import multiprocessing as mp import os import psutil nthreads = psutil . cpu_count ( logical = True ) ncores = psutil . cpu_count ( logical = False ) nthreads_per_core = nthreads // ncores nthreads_available = len ( os . sched_getaffinity ( 0 )) ncores_available = nthreads_available // nthreads_per_core assert nthreads == os . cpu_count () assert nthreads == mp . cpu_count () print ( f ' { nthreads =} ' ) print ( f ' { ncores =} ' ) print ( f ' { nthreads_per_core =} ' ) print ( f ' { nthreads_available =} ' ) print ( f ' { ncores_available =} ' )
Running that script as a scronjob in the cron qos on perlmutter would report:
cron
nthreads=256
ncores=128
nthreads_per_core=2
nthreads_available=2
ncores_available=1
nthreads=256
ncores=128
nthreads_per_core=2
nthreads_available=2
ncores_available=1

## NumPy and nested threading ¶

If your multiprocessing code makes calls to a threaded library like NumPy with threaded MKL support then you need to consider oversubscription of threads. While process affinity can be controlled to some degrees in certain contexts (e.g. Python distributions that implement os.sched_{get,set}affinity) it is generally easier to reduce the number of threads used by each process. Actually it is most advisable to set it to a single thread. In particular for OpenMP:
os.sched_{get,set}affinity)
export OMP_NUM_THREADS = 1
export OMP_NUM_THREADS = 1

## Use the spawn start method ¶

The default method used by multiprocessing to start processes on Linux is fork . We advise using the spawn start method as it is typically more robust. The following script demonstrates how to set the start method safely inside the main entrypoint (under if __name__ == '__main__': ) of a Python program:
fork
spawn
if __name__ == '__main__':
import multiprocessing as mp def addone ( x ): return x + 1 if __name__ == '__main__' : mp . set_start_method ( 'spawn' ) with mp . Pool ( 4 ) as pool : pool . map ( addone , range ( 100 ))
import multiprocessing as mp def addone ( x ): return x + 1 if __name__ == '__main__' : mp . set_start_method ( 'spawn' ) with mp . Pool ( 4 ) as pool : pool . map ( addone , range ( 100 ))

## mpi4py ¶

mpi4py provides MPI standard bindings to the Python programming language.
Here is an example of how to use mpi4py at NERSC:
#!/usr/bin/env python from mpi4py import MPI mpi_rank = MPI . COMM_WORLD . Get_rank () mpi_size = MPI . COMM_WORLD . Get_size () print ( mpi_rank , mpi_size )
#!/usr/bin/env python from mpi4py import MPI mpi_rank = MPI . COMM_WORLD . Get_rank () mpi_size = MPI . COMM_WORLD . Get_size () print ( mpi_rank , mpi_size )
This program will initialize MPI, find each MPI task's rank in the global communicator, find the total number of ranks in the global communicator, print out these two results, and exit. Finalizing MPI with mpi4py is not necessary; it happens automatically when the program exits.
Suppose we put this program into a file called "mympi.py." To run it on Perlmutter CPU nodes, we could create the following batch script in the same directory as our Python script, that we call "myjob.sh":
#!/bin/bash #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH --time=5 module load python
srun -n 256 -c 2 python mympi.py
#!/bin/bash #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH --time=5 module load python
srun -n 256 -c 2 python mympi.py
applications using mpi4py must be launched via srun
Next, we submit the batch script from the command line using sbatch, and wait for it to run:
$ sbatch myjob.sh
Submitted batch job 987654321
$ sbatch myjob.sh
Submitted batch job 987654321
After the job finishes, the output will be found in the file with a name like "slurm-987654321.out":
$ cat slurm-987654321.out
... 191 256 144 256 131 256 ... 0 256 ...
$ cat slurm-987654321.out
... 191 256 144 256 131 256 ... 0 256 ...

## mpi4py in your custom conda environment ¶

mpi4py
Do NOT conda/pip install mpi4py at NERSC
conda/pip install mpi4py
You can install mpi4py using these tools without any warnings, but your mpi4py programs just won't work at NERSC. To use Cray MPICH MPI, you'll need to build it yourself using the Cray compiler wrappers that link in Cray MPICH libraries.
In the next few sections, we demonstrate various methods for installing mpi4py in a conda environment at NERSC. For mpi4py -specific details, see the mpi4py installation docs .
mpi4py
mpi4py
mpi4py
pip
At NERSC, we recommend installing mpi4py from source using pip . For example, the following set of commands, when run in the default environment at NERSC with the PrgEnv-gnu , cray-mpich , etc. modules loaded, will build and install mpi4py in a conda environment.
mpi4py
pip
PrgEnv-gnu
cray-mpich
mpi4py
module load conda
conda create -n my_mpi4py_env
conda activate my_mpi4py_env MPICC = "cc -shared" pip install --force-reinstall --no-cache-dir --no-binary = mpi4py mpi4py
module load conda
conda create -n my_mpi4py_env
conda activate my_mpi4py_env MPICC = "cc -shared" pip install --force-reinstall --no-cache-dir --no-binary = mpi4py mpi4py
Using this method configures the mpi4py in your environment to use the cray-mpich MPI library which supports communication on Perlmutter's Slingshot 11 high speed network and interoperates with the Slurm srun command for parallel launch.
mpi4py
cray-mpich
srun
nersc-mpi4py
Alternatively, the NERSC python module inclues a minimal nersc-mp4py conda environment that can be used to bootstrap a conda environment using the conda create --clone method to create conda environments.
python
nersc-mp4py
conda create --clone
module load python
conda create --name my_mpi4py_env --clone nersc-mpi4py
conda activate my_mpi4py_env
module load python
conda create --name my_mpi4py_env --clone nersc-mpi4py
conda activate my_mpi4py_env
From there, you can use conda install to install additional conda packages.
conda install
Another option is to use conda packages that are ABI compatible with the MPI library provided by the cray-mpich-abi module at NERSC. Here's an example of how to use the "dummy" mpich package from conda-forge.
cray-mpich-abi
module load conda
conda create --name my_mpi4py_env -c conda-forge mpi4py "mpich=*=external_*"
module load conda
conda create --name my_mpi4py_env -c conda-forge mpi4py "mpich=*=external_*"
When you use this environment you will also need to load the cray-mpich-abi module, for example:
cray-mpich-abi
conda activate my_mpi4py_env
module load cray-mpich-abi
conda activate my_mpi4py_env
module load cray-mpich-abi
Note this method may not quite work "out of the box" and may require some experimentation to check version compatibility or additional configuration to enable GPU aware communication.

## Inspect MPI library version ¶

After installing mpi4py in your environment, you may want to inspect the version of the MPI library at run time to confirm it matches your expectations. For example:
mpi4py
elvis@login01:~> salloc -N 1 -t 30 -C cpu -q interactive
...
elvis@nid00195:~> module load python
elvis@nid00195:~> srun python -c "from mpi4py import MPI;print(MPI.Get_library_version())" MPI VERSION : CRAY MPICH version 8 .1.25.17 ( ANL base 3 .4a2 ) MPI BUILD INFO : Sun Feb 26 15 :15 2023 ( git hash aecd99f )
elvis@login01:~> salloc -N 1 -t 30 -C cpu -q interactive
...
elvis@nid00195:~> module load python
elvis@nid00195:~> srun python -c "from mpi4py import MPI;print(MPI.Get_library_version())" MPI VERSION : CRAY MPICH version 8 .1.25.17 ( ANL base 3 .4a2 ) MPI BUILD INFO : Sun Feb 26 15 :15 2023 ( git hash aecd99f )

## Using mpi4py in a Shifter container ¶

mpi4py
When a large number of Python tasks are simultaneously launched with mpi4py, the result is many tasks trying to open the same files at the same time, causing filesystem contention and performance degradation. mpi4py applications running at the scale of a few hundred or a thousand tasks may take an unacceptable amount of time simply starting up.
Using mpi4py in a Shifter container is our recommended solution to this problem. We provide Python in Shifter examples and a specific mpi4py in Shifter example .

## Dask ¶

Dask is a task-based system in which a scheduler assigns work to workers. It is robust to failure and provides a nice bokeh-based application dashboard. It can be used to scale to multinode CPU and GPU systems. You can find more information on the NERSC Dask page .

## Parallel I/O with h5py ¶

You can use h5py for either serial or parallel I/O.
For more general information about HDF5 at NERSC please see the NERSC HDF5 page .
If you would like to use h5py for parallel I/O, you have two choices:
build h5py against mpi4py in your custom conda environment;
use the nersc-h5py conda environment that we provide, or clone it if you want to add other packages.
nersc-h5py
Both options are based on packages built against the GNU compiler and Cray MPICH, so if you want a build with a different compiler or MPI library, you'll have to recompile both mpi4py and h5py from scratch.
HDF5 File Locking
You will have to disable file locking if you are writing to a filesystem other than $SCRATCH .
$SCRATCH
export HDF5_USE_FILE_LOCKING = FALSE
export HDF5_USE_FILE_LOCKING = FALSE

## Pre-built h5py conda environment ¶

To use the conda environment that we provide:
module load python
conda activate nersc-h5py
module load python
conda activate nersc-h5py
And you are good to go; you can test it with a smoketest, see below .
You cannot install other packages in that conda environment, though, since it's read-only, but you can clone it and work on it:
module load python
conda create --name h5pyenv --clone nersc-h5py
conda activate h5pyenv

conda install ...
module load python
conda create --name h5pyenv --clone nersc-h5py
conda activate h5pyenv

conda install ...

## Building h5py from source ¶

Build h5py (and mpi4py ) from source at NERSC with support for multinode parallel IO using cray-hdf5-parallel and cray-mpich . These instructions (adapted from the h5py documentation ) assume you are starting from the NERSC default environment with at least the PrgEnv-gnu and cray-mpich modules already loaded.
h5py
mpi4py
cray-hdf5-parallel
cray-mpich
h5py
PrgEnv-gnu
cray-mpich
First, load the conda and cray-hdf5-parallel modules:
conda
cray-hdf5-parallel
module load cray-hdf5-parallel
module load conda
module load cray-hdf5-parallel
module load conda
Create and activate a conda environment with h5py dependencies (except for mpi4py which we'll build from source in the next step):
h5py
mpi4py
conda create -n h5pyenv python numpy cython pkgconfig setuptools
conda activate h5pyenv
conda create -n h5pyenv python numpy cython pkgconfig setuptools
conda activate h5pyenv
Build mpi4py from source with the cray compiler wrapper to include support for multinode parallel communication at NERSC:
mpi4py
MPICC = "cc -shared" pip install --force-reinstall --no-cache-dir --no-binary = mpi4py mpi4py
MPICC = "cc -shared" pip install --force-reinstall --no-cache-dir --no-binary = mpi4py mpi4py
Build h5py from source with the cray compiler wrapper to include support for multinode parallel IO at NERSC:
h5py
HDF5_MPI = ON CC = cc pip install -v --force-reinstall --no-cache-dir --no-binary = h5py --no-build-isolation --no-deps h5py
HDF5_MPI = ON CC = cc pip install -v --force-reinstall --no-cache-dir --no-binary = h5py --no-build-isolation --no-deps h5py
We used a few pip install flags to help achieve the desired outcome in this case. Not all were strictly necessary but they may come in handy in case you run into any issues.

## Smoketest for h5py ¶

To test a parallel build of h5py we need to use the compute nodes, since mpi4py doesn't work on login nodes. Let's get 2 interactive compute nodes, with 2 processors each and activate the h5py environment we just cloned or built:
salloc -N 2 --ntasks-per-node 2 -t 10 -C cpu -q interactive
module load conda
conda activate h5pyenv
salloc -N 2 --ntasks-per-node 2 -t 10 -C cpu -q interactive
module load conda
conda activate h5pyenv
We'll use this test program described in the h5py docs :
from mpi4py import MPI import h5py rank = MPI . COMM_WORLD . rank # The process ID (integer 0-3 for a 4-process job) with h5py . File ( 'test.h5' , 'w' , driver = 'mpio' , comm = MPI . COMM_WORLD ) as f : dset = f . create_dataset ( 'test' , ( 4 ,), dtype = 'i' ) dset [ rank ] = rank
from mpi4py import MPI import h5py rank = MPI . COMM_WORLD . rank # The process ID (integer 0-3 for a 4-process job) with h5py . File ( 'test.h5' , 'w' , driver = 'mpio' , comm = MPI . COMM_WORLD ) as f : dset = f . create_dataset ( 'test' , ( 4 ,), dtype = 'i' ) dset [ rank ] = rank
We can run this test with the 4 mpi ranks requested:
srun python test_h5py.py
srun python test_h5py.py
If we now look at the file we wrote with h5dump test.h5 it should look like this:
h5dump test.h5
HDF5 "test.h5" { GROUP "/" { DATASET "test" { DATATYPE H5T_STD_I32LE DATASPACE SIMPLE { ( 4 ) / ( 4 ) } DATA { ( 0 ) : 0 , 1 , 2 , 3 } } } }
HDF5 "test.h5" { GROUP "/" { DATASET "test" { DATATYPE H5T_STD_I32LE DATASPACE SIMPLE { ( 4 ) / ( 4 ) } DATA { ( 0 ) : 0 , 1 , 2 , 3 } } } }
Great! Our 4 mpi ranks each wrote part of the HDF5 file.

## PyOMP ¶

PyOMP is a new and experimental framework
PyOMP is relatively new and undergoing active development. We welcome any interested users to give PyOMP a try, but users should be aware that this may not be suitable for production workloads. Please don't hesitate to contact NERSC with any questions or comments about using PyOMP.
PyOMP is a new project to allow Python programmers to use OpenMP directives in their Python code. These directives can be used to achieve low-level thread parallelism in loops, for example. Right now PyOMP provides CPU-only support but eventually plans to add GPU support.
Users can install an experimental development version of numba with PyOMP support from the drtodd13 conda channel using the following commands.
drtodd13
> module load python
> conda create -n pyomp python numba -c drtodd13 -c conda-forge --override-channels
> module load python
> conda create -n pyomp python numba -c drtodd13 -c conda-forge --override-channels
Confirm that numba was installed from the drtodd13 conda channel:
numba
drtodd13
> conda activate pyomp ( pyomp ) > conda list | grep numba # Name   Version         Build                                 Channel ...
numba 0 .55.0dev0 np1.11py3.7hc13618b_gcd8f3afa0_488 drtodd13
...
> conda activate pyomp ( pyomp ) > conda list | grep numba # Name   Version         Build                                 Channel ...
numba 0 .55.0dev0 np1.11py3.7hc13618b_gcd8f3afa0_488 drtodd13
...

## PyOMP in Shifter ¶

Users can also use a NERSC Shifter image that already contains PyOMP . The image registry.nersc.gov/library/nersc/pyomp:0.55 is already available on Perlmutter. To test on a login node, a user can
registry.nersc.gov/library/nersc/pyomp:0.55
elvis@login01:~> OMP_NUM_THREADS = 2 spyomp hello_par.py
elvis@login01:~> OMP_NUM_THREADS = 2 spyomp hello_par.py
To use in a job:
elvis@login01:~> cat job2.sh #!/bin/bash #SBATCH --image=registry.nersc.gov/library/nersc/pyomp:0.55 #SBATCH --qos=debug #SBATCH -N 1 #SBATCH -C cpu export OMP_NUM_THREADS = 128 spyomp hello_par.py
elvis@login01:~> sbatch job2.sh
elvis@login01:~> cat job2.sh #!/bin/bash #SBATCH --image=registry.nersc.gov/library/nersc/pyomp:0.55 #SBATCH --qos=debug #SBATCH -N 1 #SBATCH -C cpu export OMP_NUM_THREADS = 128 spyomp hello_par.py
elvis@login01:~> sbatch job2.sh
where the hello_par.py Python script is:
hello_par.py
from numba import njit from numba.openmp import openmp_context as openmp @njit def hello (): with openmp ( "parallel" ): print ( "hello" ) print ( "world" ) hello ()
from numba import njit from numba.openmp import openmp_context as openmp @njit def hello (): with openmp ( "parallel" ): print ( "hello" ) print ( "world" ) hello ()
Note both of these examples make use of the spyomp wrapper, which is a simple alias to the registry.nersc.gov/library/nersc/pyomp:0.55 image and Shifter command, which is accessible to all users:
spyomp
registry.nersc.gov/library/nersc/pyomp:0.55
elvis@login01:~> cat $( which spyomp ) #!/bin/bash if echo $* | grep -e "-h" -q then echo 'Usage: spyomp is a NERSC wrapper to use a PyOMP shifter image to run PyOMP application codes' echo 'spyomp pyomp_code.py' echo 'or OMP_NUM_THREADS=<value> spyomp pyomp_code.py' else shifter --image = registry.nersc.gov/library/nersc/pyomp:0.55 python " $@ " fi
elvis@login01:~> cat $( which spyomp ) #!/bin/bash if echo $* | grep -e "-h" -q then echo 'Usage: spyomp is a NERSC wrapper to use a PyOMP shifter image to run PyOMP application codes' echo 'spyomp pyomp_code.py' echo 'or OMP_NUM_THREADS=<value> spyomp pyomp_code.py' else shifter --image = registry.nersc.gov/library/nersc/pyomp:0.55 python " $@ " fi
For more information about using Shifter at NERSC, please see our Shifter documentation .

## PyOMP Example ¶

Here is a simple example using openmp in numba based on an example from the PyOMP project repo .
from numba import njit from numba.openmp import openmp_context as openmp @njit def pi_numba_openmp ( num_steps ): step = 1.0 / num_steps sum = 0.0 with openmp ( "parallel for private(x) reduction(+:sum)" ): for i in range ( num_steps ): x = ( i + 0.5 ) * step sum += 4.0 / ( 1.0 + x * x ) pi = step * sum return pi pi = pi_numba_openmp ( 1_000_000_000 ) print ( pi )
from numba import njit from numba.openmp import openmp_context as openmp @njit def pi_numba_openmp ( num_steps ): step = 1.0 / num_steps sum = 0.0 with openmp ( "parallel for private(x) reduction(+:sum)" ): for i in range ( num_steps ): x = ( i + 0.5 ) * step sum += 4.0 / ( 1.0 + x * x ) pi = step * sum return pi pi = pi_numba_openmp ( 1_000_000_000 ) print ( pi )
Aftering creating and activiting your pyomp conda environment, you can run the code with:
( pyomp ) > export OMP_NUM_THREADS = 8 ( pyomp ) > python pi_loop_openmp.py 3 .1415926535897687
( pyomp ) > export OMP_NUM_THREADS = 8 ( pyomp ) > python pi_loop_openmp.py 3 .1415926535897687
where we use the environment variable OMP_NUM_THREADS to specify the number threads to use for parallel regions.
OMP_NUM_THREADS
If you have questions or feedback about PyOMP, please let us know by submitting a ticket at help.nersc.gov .