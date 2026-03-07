# Source: https://docs.nersc.gov/jobs/best-practices/

## Best Practices for Jobs ¶


## Do Not Run Production Jobs in Global Homes or CFS ¶

As a general best practice, users should do production runs from $SCRATCH instead of $HOME or $CFS .
$SCRATCH
$HOME
$CFS
$HOME is meant for permanent and relatively small storage. It is not tuned to perform well for parallel jobs. Home is perfect for storing files such as source codes and shell scripts, etc. Please note that while building software in /global/home is generally good, it is best to install dynamic libraries that are used on compute nodes in global common for best performance.
$HOME
$CFS is meant for sharing of data. Sharing of software should be done in Global Common .
$CFS
Global Common
$SCRATCH is meant for large and temporary storage. It is optimized for read and write operations. $SCRATCH is perfect for staging data and performing parallel computations. Running in $SCRATCH also helps to improve the responsiveness of the global file systems (global homes and global project) in general.
$SCRATCH
$SCRATCH
$SCRATCH

## Specify account ¶

For users who are members of multiple NERSC repositories charges are made to the default account, as set in Iris , unless the #SBATCH --account=<NERSC repository> flag has been set. It is good practice to always set the account flag to ensure the appropriate allocation is charged.
#SBATCH --account=<NERSC repository>

## Time Limits ¶

Due to backfill scheduling, short and variable-length jobs generally start quickly resulting in much better job throughput.
#SBATCH --time-min=<lower_bound> #SBATCH --time=<upper_bound>
#SBATCH --time-min=<lower_bound> #SBATCH --time=<upper_bound>

## Long Running Jobs ¶

Simulations which must run for a long period of time achieve the best throughput when composed of many small jobs utilizing checkpoint/restart chained together.
Example: job chaining with dependency jobs
Example: variable-time jobs with checkpoint/restart

## Limit Your Queries to the Batch System ¶

We recommend you limit the rate at which your jobs query the batch system to an aggregate of 1 - 2 times / minutes. This includes all Slurm queries such as squeue , sbatch , srun , or other Slurm commands. Keep in mind this is an aggregate rate across all your jobs, so if you have a single job that queries once a minute but 500 of these jobs start at once Slurm will see a rate of 500 queries / minute, so please scale your rate accordingly.
squeue
sbatch
srun
If too many users query the scheduler at once it can become overwhelmed and become unable to schedule user jobs. To avoid this, Slurm has implemented an algorithm to limit users who make a very high rate of Slurm queries. Once a user exceeds this rate, the scheduler will pause briefly before responding to the query. This means that if you have a high rate of Slurm queries, you will be spending your compute time waiting for a response from the scheduler which is not an efficient use of compute time. If you need to get the information from squeue, you can switch to sacct .

## Improve Efficiency by Preparing User Environment Before Running ¶

In general, compute nodes are optimized for processing data and running simulations. Users should use login nodes for compilations, environment setup and preprocessing small inputs, in order to utilize compute resources efficiently.
Using the Linux here document as in the example below will run those commands to prepare the user environment for the batch job on the login node to help improve job efficiency and save computing cost of the batch job. It can also help to alleviate the burden on the global home file system. This script also keeps the user environment needed for the batch job in a single file.
Example
This is an example of a script to prepare the user environment on a login node, propagate this environment to a batch job, and submit the batch job. This can be accomplished in a single script.
You could do so by preparing a file named prepare-env.sh in the example below, and running it as ./prepare-env.sh on a login node. This script:
prepare-env.sh
./prepare-env.sh
Sets up the user environment for the batch job first on a login node, such as loading modules, setting environment variables, or copying input files, etc.;
Creates a batch script named prepare-env.sl ;
prepare-env.sl
Submits prepare-env.sl : this job will inherit the user environment just set earlier in the script.
prepare-env.sl
#!/bin/bash -l

# Submit this script as: "./prepare-env.sh" instead of "sbatch prepare-env.sh"

# Prepare user env needed for Slurm batch job
# such as module load, setup runtime environment variables, or copy input files, etc.
# Basically, these are the commands you usually run ahead of the srun command 

module load cray-hdf5
export OMP_NUM_THREADS=4

# Generate the Slurm batch script below with the here document, 
# then when sbatch the script later, the user env set up above will run on the login node
# instead of on a head compute node (if included in the Slurm batch script),
# and inherited into the batch job.

cat << EOF > prepare-env.sl 
#!/bin/bash
#SBATCH -t 30:00
#SBATCH -N 2
#SBATCH -q debug
#SBATCH -C cpu

srun -n 16 -c 32 --cpu_bind=cores ./myapp.exe 

# Other commands needed after srun, such as copy your output filies,
# should still be included in the Slurm script.
cp <my_output_file> <target_location>/.
EOF

# Now submit the batch job
sbatch prepare-env.sl
#!/bin/bash -l

# Submit this script as: "./prepare-env.sh" instead of "sbatch prepare-env.sh"

# Prepare user env needed for Slurm batch job
# such as module load, setup runtime environment variables, or copy input files, etc.
# Basically, these are the commands you usually run ahead of the srun command 

module load cray-hdf5
export OMP_NUM_THREADS=4

# Generate the Slurm batch script below with the here document, 
# then when sbatch the script later, the user env set up above will run on the login node
# instead of on a head compute node (if included in the Slurm batch script),
# and inherited into the batch job.

cat << EOF > prepare-env.sl 
#!/bin/bash
#SBATCH -t 30:00
#SBATCH -N 2
#SBATCH -q debug
#SBATCH -C cpu

srun -n 16 -c 32 --cpu_bind=cores ./myapp.exe 

# Other commands needed after srun, such as copy your output filies,
# should still be included in the Slurm script.
cp <my_output_file> <target_location>/.
EOF

# Now submit the batch job
sbatch prepare-env.sl

## Performance at Scale ¶


## Install Your Code in the Right Place ¶

For large scale jobs at NERSC, putting your code into a container will always be the most performant option.
If a container won't work for your use case and your software stack is very small, your next best option is to use the Slurm sbcast command to copy the executable to a local path on the compute nodes allocated to the job, instead of loading it onto the compute nodes from a slow file system such as the home.
sbcast
Users can copy the executable to the compute nodes before the actual computation using the Slurm sbcast command or the srun --bcast flag. Making the executable available local to the compute node, e.g. in /tmp could speed up the job startup time compared to running executables from a network file system.
sbcast
srun
--bcast
/tmp
For example, assuming exe_on_slow_fs is the executable filename, which resides on a slow file system such as the user home, you can modify the line of srun in your submit script from this:
exe_on_slow_fs
srun
srun exe_on_slow_fs
srun exe_on_slow_fs
to this:
srun --bcast = /tmp/ ${ USER } _exe_filename exe_on_slow_fs
srun --bcast = /tmp/ ${ USER } _exe_filename exe_on_slow_fs
or to this:
sbcast exe_on_slow_fs /tmp/ ${ USER } _exe_filename srun /tmp/ ${ USER } _exe_filename
sbcast exe_on_slow_fs /tmp/ ${ USER } _exe_filename srun /tmp/ ${ USER } _exe_filename
Make sure to choose a temporary file name unique to your computation (e.g. include your username with the variable $USER ), or you may receive permission denied errors if trying to overwrite someone else's files.
$USER
If your executable loads libraries that are also installed on slow file systems, you will need to add an option to copy these libraries to the compute nodes as well:
sbcast --send-libs exe_on_slow_fs /tmp/ ${ USER } _exe_filename export LD_LIBRARY_PATH = /tmp/ ${ USER } _exe_filename_libs: $LD_LIBRARY_PATH srun /tmp/ ${ USER } _exe_filename
sbcast --send-libs exe_on_slow_fs /tmp/ ${ USER } _exe_filename export LD_LIBRARY_PATH = /tmp/ ${ USER } _exe_filename_libs: $LD_LIBRARY_PATH srun /tmp/ ${ USER } _exe_filename
However, if your executable is compiled with the rpath option, it will ignore the LD_LIBRARY_PATH variable and still access libraries from the slower file system.
rpath
LD_LIBRARY_PATH
Tip
There is no real downside to broadcasting the executable with Slurm, so it can be used with jobs at any scale, especially if you experience timeout errors associated with MPI_Init() .
MPI_Init()
Tip
Besides the executable, you can also sbcast other large files, such as input files, shared libraries, etc. It would be easier to create a tar file to sbcast , then untar on the compute nodes before the actual srun instead of sbcast ing multiple individual files.
sbcast
sbcast
untar
srun
sbcast
Tip
You could also set the destination to be a file path (such as /tmp/${$USER}_dir/ ) instead of a file name. Make sure the file path already exists (or to create one) and to include the " / " at the end of the path name in the sbcast and srun commands.
/tmp/${$USER}_dir/
/
sbcast
srun
If a container won't work for your use case and your software stack is very complex (e.g. a conda environment), then you should install it into the Global Common File System.
Perlmutter has a dedicated large, local, parallel scratch file system. Since the scratch file system is intended for temporary uses such as storage of checkpoints or application input and output, instead of installing your code into Scratch we recommend to copy to Scratch before running your job. Data and I/O intensive applications should use the local scratch file system.
Warning
The Scratch File System is not backed up and old files are subject to purging .

## Read Your Data From the Right Place ¶

If your job reads large volumes of data, the fastest file system will almost always be Perlmutter Scratch . However, if many of the processes in your jobs repeatedly read in the same file (e.g. a configuration file), you may see a large speedup by using a read-only DVS mount. On Perlmutter CFS has a corresponding read-only mount at /dvs_ro/cfs , respectively. We recommend using this for data that is being read during a job that is not being actively changed. The DVS mount of this file system will cache data for 30 seconds by default, so if data is being changed, you may see unexpected results.
/dvs_ro/cfs

## File System Licenses ¶

Users should specify the file systems their jobs will use with the sbatch license flag, -L or --licenses . A batch job will not start if any of the specified file systems are unavailable due to maintenance or an outage. The following example specifies that a job uses both the scratch and community file systems.
sbatch
-L
--licenses
scratch
#SBATCH -L scratch,cfs
#SBATCH -L scratch,cfs
Or
#SBATCH --licenses=scratch,cfs
#SBATCH --licenses=scratch,cfs

## Available Licenses ¶

scratch (or SCRATCH )
scratch
SCRATCH
cfs
cfs
dna
dna
cvmfs
cvmfs
hpss (Perlmutter only)
hpss
Licenses can also be added or adjusted after submission with scontrol update job=<jobid> Licenses=<comma separated list of licenses>
scontrol update job=<jobid> Licenses=<comma separated list of licenses>

## Core Specialization ¶

Core specialization is a feature designed to isolate system overhead (system interrupts, etc.) to designated cores on a compute node. Setting aside 1 or 2 cores for core specialization is recommended.
The srun flag for core specialization is -S or --core-spec . It only works in a batch script with sbatch . It can not be requested as a flag with salloc for interactive jobs, since salloc is already a wrapper script for srun .
srun
-S
--core-spec
sbatch
salloc
salloc
srun
Example

## Process Placement ¶

Several mechanisms exist to control process placement on NERSC's Cray systems. Application performance can depend strongly on placement depending on the communication pattern and other computational characteristics.
Examples below are run on Perlmutter.

## Default ¶

elvis@perlmutter$ salloc -N 4 -C cpu -q interactive -t 20 :00 elvis@nid004175$ srun -n 8 -c 2 check-gnu.pm | sort -nk 4 Hello from rank 0, on nid004175. (core affinity = 0,128) Hello from rank 1, on nid004175. (core affinity = 16,144) Hello from rank 2, on nid004622. (core affinity = 0,128) Hello from rank 3, on nid004622. (core affinity = 16,144) Hello from rank 4, on nid006290. (core affinity = 0,128) Hello from rank 5, on nid006290. (core affinity = 16,144) Hello from rank 6, on nid006430. (core affinity = 0,128) Hello from rank 7, on nid006430. (core affinity = 16,144)
elvis@perlmutter$ salloc -N 4 -C cpu -q interactive -t 20 :00 elvis@nid004175$ srun -n 8 -c 2 check-gnu.pm | sort -nk 4 Hello from rank 0, on nid004175. (core affinity = 0,128) Hello from rank 1, on nid004175. (core affinity = 16,144) Hello from rank 2, on nid004622. (core affinity = 0,128) Hello from rank 3, on nid004622. (core affinity = 16,144) Hello from rank 4, on nid006290. (core affinity = 0,128) Hello from rank 5, on nid006290. (core affinity = 16,144) Hello from rank 6, on nid006430. (core affinity = 0,128) Hello from rank 7, on nid006430. (core affinity = 16,144)

## MPICH_RANK_REORDER_METHOD ¶

MPICH_RANK_REORDER_METHOD
The MPICH_RANK_REORDER_METHOD environment variable is used to specify other types of MPI task placement. For example, setting it to 0 results in a round-robin placement:
MPICH_RANK_REORDER_METHOD
elvis@nid004175$ MPICH_RANK_REORDER_METHOD = 0 srun -n 8 -c 2 check-mpi.gnu.pm | sort -nk 4 Hello from rank 0, on nid004175. (core affinity = 1,129) Hello from rank 1, on nid004622. (core affinity = 1,129) Hello from rank 2, on nid006290. (core affinity = 1,129) Hello from rank 3, on nid006430. (core affinity = 1,129) Hello from rank 4, on nid004175. (core affinity = 17,145) Hello from rank 5, on nid004622. (core affinity = 17,145) Hello from rank 6, on nid006290. (core affinity = 17,145) Hello from rank 7, on nid006430. (core affinity = 17,145)
elvis@nid004175$ MPICH_RANK_REORDER_METHOD = 0 srun -n 8 -c 2 check-mpi.gnu.pm | sort -nk 4 Hello from rank 0, on nid004175. (core affinity = 1,129) Hello from rank 1, on nid004622. (core affinity = 1,129) Hello from rank 2, on nid006290. (core affinity = 1,129) Hello from rank 3, on nid006430. (core affinity = 1,129) Hello from rank 4, on nid004175. (core affinity = 17,145) Hello from rank 5, on nid004622. (core affinity = 17,145) Hello from rank 6, on nid006290. (core affinity = 17,145) Hello from rank 7, on nid006430. (core affinity = 17,145)
There are other modes available with the MPICH_RANK_REORDER_METHOD environment variable, including one which lets the user provide a file called MPICH_RANK_ORDER which contains a list of each task's placement on each node. These options are described in detail in the intro_mpi man page.
MPICH_RANK_REORDER_METHOD
MPICH_RANK_ORDER
intro_mpi
grid_order
For MPI applications which perform a large amount of nearest-neighbor communication, e.g., stencil-based applications on structured grids, Cray provides a tool in the perftools-base module called grid_order which can generate a MPICH_RANK_ORDER file automatically by taking as parameters the dimensions of the grid, core count, etc. For example, to place MPI tasks in row-major order on a Cartesian grid of size (4, 4, 4) , using 32 tasks per node on Perlmutter:
perftools-base
grid_order
MPICH_RANK_ORDER
perlmutter$ module load perftools-base
perlmutter$ grid_order -R -c 32 -g 4,4,4
# grid_order -R -Z -c 32 -g 4,4,4
# Region 3: 0,0,1 (0..63)
0,1,2,3,16,17,18,19,32,33,34,35,48,49,50,51,4,5,6,7,20,21,22,23,36,37,38,39,52,53,54,55
8,9,10,11,24,25,26,27,40,41,42,43,56,57,58,59,12,13,14,15,28,29,30,31,44,45,46,47,60,61,62,63
perlmutter$ module load perftools-base
perlmutter$ grid_order -R -c 32 -g 4,4,4
# grid_order -R -Z -c 32 -g 4,4,4
# Region 3: 0,0,1 (0..63)
0,1,2,3,16,17,18,19,32,33,34,35,48,49,50,51,4,5,6,7,20,21,22,23,36,37,38,39,52,53,54,55
8,9,10,11,24,25,26,27,40,41,42,43,56,57,58,59,12,13,14,15,28,29,30,31,44,45,46,47,60,61,62,63
One can then save this output to a file called MPICH_RANK_ORDER and then set MPICH_RANK_REORDER_METHOD=3 before running the job, which tells Cray MPI to read the MPICH_RANK_ORDER file to set the MPI task placement. For more information, please see the man page man grid_order (available when the perftools-base module is loaded) on Perlmutter.
MPICH_RANK_ORDER
MPICH_RANK_REORDER_METHOD=3
MPICH_RANK_ORDER
man grid_order
perftools-base

## Hugepages ¶

Huge pages are virtual memory pages which are bigger than the default page size of 4K bytes. Huge pages can improve memory performance for common access patterns on large data sets since it helps to reduce the number of virtual to physical address translations than compared with using the default 4K. Huge pages also increase the maximum size of data and text in a program accessible by the high speed network, and reduce the cost of accessing memory, such as in the case of many MPI_Alltoall operations. Using hugepages can help to reduce the application runtime variability .
MPI_Alltoall
To use hugepages for an application (with the 2M hugepages as an example):
module load craype-hugepages2M
cc -o mycode.exe mycode.c
module load craype-hugepages2M
cc -o mycode.exe mycode.c
And also load the same hugepages module at runtime.
Due to the hugepages memory fragmentation issue, applications may get "Cannot allocate memory" warnings or errors when there are not enough hugepages on the compute node, such as:
libhugetlbfs [nid000xx:xxxxx]: WARNING: New heap segment map at 0x10000000 failed: Cannot allocate memory
libhugetlbfs [nid000xx:xxxxx]: WARNING: New heap segment map at 0x10000000 failed: Cannot allocate memory

## When to Use Huge Pages ¶

For MPI applications, map the static data and/or heap onto huge pages.
For an application which uses shared memory, which needs to be concurrently registered with the high speed network drivers for remote communication.
For SHMEM applications, map the static data and/or private heap onto huge pages.
For applications written in Unified Parallel C, Coarray Fortran, and other languages based on the PGAS programming model, map the static data and/or private heap onto huge pages.
For an application doing heavy I/O.
To improve memory performance for common access patterns on large data sets.

## When to Avoid Huge Pages ¶

Applications sometimes consist of many steering programs in addition to the core application. Applying huge page behavior to all processes would not provide any benefit and would consume huge pages that would otherwise benefit the core application. The runtime environment variable HUGETLB_RESTRICT_EXE can be used to specify the subset of the programs to use hugepages.
Applications sometimes consist of many steering programs in addition to the core application. Applying huge page behavior to all processes would not provide any benefit and would consume huge pages that would otherwise benefit the core application. The runtime environment variable HUGETLB_RESTRICT_EXE can be used to specify the subset of the programs to use hugepages.
HUGETLB_RESTRICT_EXE
For certain applications if using hugepages either causes issues or slowing down performances, users can explicitly unload the craype-hugepages2M module. One such example is that when an application forks more subprocesses (such as pthreads) and allocate memory, the newly allocated memory are the small 4K pages.
For certain applications if using hugepages either causes issues or slowing down performances, users can explicitly unload the craype-hugepages2M module. One such example is that when an application forks more subprocesses (such as pthreads) and allocate memory, the newly allocated memory are the small 4K pages.
craype-hugepages2M

## Transparent Huge Pages ¶

Linux Kernel supports Transparent Huge Pages (THP) . THP is an alternative mean of using huge pages for the backing of virtual memory with huge pages that supports the automatic promotion and demotion of page sizes and without the shortcomings of hugetlbfs .
Linux Kernel supports Transparent Huge Pages (THP) . THP is an alternative mean of using huge pages for the backing of virtual memory with huge pages that supports the automatic promotion and demotion of page sizes and without the shortcomings of hugetlbfs .
To disable THP support in a compute job, one can add the no-thp setting to --perf option (e.g --perf=no-thp,<other_perf_options> ) with salloc or in a job script with #SBATCH --perf=no-thp directives.
To disable THP support in a compute job, one can add the no-thp setting to --perf option (e.g --perf=no-thp,<other_perf_options> ) with salloc or in a job script with #SBATCH --perf=no-thp directives.
no-thp
--perf
--perf=no-thp,<other_perf_options>
salloc
#SBATCH --perf=no-thp

## Task Packing ¶

Users requiring large numbers of single-task jobs have several options at NERSC. The options include:
Submitting jobs to the shared QOS ,
Using a workflow tool to combine the tasks into one larger job,
Using job arrays to submit many individual jobs which look very similar.
If you have a large number of independent serial jobs (that is, the jobs do not have dependencies on each other), you may wish to pack the individual tasks into one bundled Slurm job to help with queue throughput. Packing multiple tasks into one Slurm job can be done via multiple srun commands in the same job script ( example ).
srun