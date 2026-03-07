# Source: https://docs.nersc.gov/current/

## Current known issues ¶


## Perlmutter ¶

Please visit the timeline page for more information about changes we've made in our recent upgrades.
NERSC has automated monitoring that tracks failed nodes, so please only open tickets for node failures if the node consistently has poor performance relative to other nodes in the job or if the node repeatedly causes your jobs to fail.

## New issues ¶

numba.cuda
numba.cuda users may be affected by an update to the 580 nvidia driver on Perlmutter which may manifest as numba cuda driver api errors or segmentation faults in environments created before Dec 2025 ( numba<0.63 ).
numba.cuda
numba<0.63
We recommend numba.cuda users create a new environment with either numba>=0.63 or numba-cuda (see tip below). Updating an existing environment is often non-trivial so we recommend creating a new environment.
numba.cuda
numba>=0.63
numba-cuda
NERSC staff have developed a workaround for those that are unable to create a new environment with an updated version of numba or add the numba-cuda package to their environment just yet. The workaround is activated by loading the numba-cuda-580-patch module. The module adds a path to the PYTHONPATH environment variable which points to a usercustomize module that will load numba.cuda and apply a patch during python process startup before interacting with the nvidia driver and crashing.
numba
numba-cuda
numba-cuda-580-patch
PYTHONPATH
usercustomize
numba.cuda
numba.cuda transition to numba-cuda
numba.cuda
numba-cuda
The numba.cuda submodule is currently in a transition from the numba project to an nvidia-managed numba-cuda project. Looking forward, we recommend numba.cuda users migrate to the nvidia-managed numba-cuda project. For now at least, it seems users can continue using the numba.cuda target provided by the numba package but will require numba>=0.63 to avoid this issue with nvidia driver update on Perlmutter.
numba.cuda
numba-cuda
numba.cuda
numba-cuda
numba.cuda
numba
numba>=0.63
numba 0.63 release notes nvidia 580 crash fix
numba
numba-cuda install docs
numba-cuda
Many Python environment management tools provide some sort of command (e.g. conda list , pip list , etc) that can be used to check which packages and versions are installed in your environment. If you have numba installed, you can also check the version of numba in your environment with:
conda list
pip list
numba
numba
numba -s | grep -i ^Numba
numba -s | grep -i ^Numba
(If you see "command not found", numba is not in your environment 🙂)
numba
The following test can be used to trigger the error with a problematic environment:
python3 -c 'from numba import cuda; cuda.synchronize()'
python3 -c 'from numba import cuda; cuda.synchronize()'

## Ongoing issues ¶

Use of the --signal= option in slurm can result in unexpected behavior.
--signal=
slurm
We have a pending fix for this that we hope will address the issue.
We suggest not using this option until the problem can be addressed.
BIND MOUNT FAILED
Shifter users may see errors about BIND MOUNT FAILED if they attempt to volume mount directories that are not world executable. We have some workarounds for this issue .
BIND MOUNT FAILED
NVIDIA Data Center GPU Manager (dcgm) is a light weight tool to measure and monitor GPU utilization and comprehensive diagnostics of GPU nodes on a cluster. NERSC will be using this tool to measure application utilization and monitor the status of the machine. Due to current hardware limitations, collecting profiling metrics using performance tools such as Nsight-Compute, TAU, HPCToolkit applications that require acess to hardware counters will conflict with the DCGM instance running on the system.
To invoke performance collection with ncu one must add dcgmi profile --pause / --resume to your scripts (this script will work for single node or multiple node runs):
ncu
dcgmi profile --pause / --resume
srun --ntasks-per-node 1 dcgmi profile --pause
srun <Slurm flags> ncu -o <filename> <other Nsight Compute flags> <program> <program arguments>
srun --ntasks-per-node 1 dcgmi profile --resume
srun --ntasks-per-node 1 dcgmi profile --pause
srun <Slurm flags> ncu -o <filename> <other Nsight Compute flags> <program> <program arguments>
srun --ntasks-per-node 1 dcgmi profile --resume
Running profiler on multiple nodes
The DCGM instance on each node must be paused before running the profiler. Please note that you should only use 1 task to pause the dcgm instance as shown above.

## Past Issues ¶

For updates on past issues affecting Perlmutter, see the timeline page .