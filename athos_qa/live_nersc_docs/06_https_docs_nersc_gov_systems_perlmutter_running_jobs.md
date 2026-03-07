# Source: https://docs.nersc.gov/systems/perlmutter/running-jobs/

## Running Jobs on Perlmutter ¶

Perlmutter uses Slurm for batch job scheduling. Charging for jobs on Perlmutter began on October 28, 2022.
For general information on how to submit jobs using Slurm and monitor jobs, etc., see:
Slurm
Monitoring Jobs
Interactive Jobs
Replacing cron jobs with scrontab
scrontab
Perlmutter Queue Policies

## Tips and Tricks ¶


## To allocate resources using salloc or sbatch please use the correct values ¶

salloc
sbatch
sbatch
salloc
-A
m9999
m9999
-C
gpu
gpu&hbm80g
cpu
-c
For Slurm batch script, you need to specify the project name with Slurm's -A <project> or --account=<project> flag. Failing to do so so may result in output such as the following from sbatch :
-A <project>
--account=<project>
sbatch
sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
GPU nodes and CPU nodes at NERSC are allocated separately, and are charged separately too. CPU jobs will be charged against the project's CPU allocation hours, and GPU jobs will be charged against the project's GPU allocation hours.
To request GPU nodes, the -C gpu or --constraint=gpu flag must be set in your script or on the command line when submitting a job (e.g., #SBATCH -C gpu ). To run on CPU-only nodes, use the -C cpu instead. Failing to do so may result in output such as the following from sbatch :
-C gpu
--constraint=gpu
#SBATCH -C gpu
-C cpu
sbatch
sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
Higher-bandwidth memory GPU nodes
Jobs may explicitly request to run on up to 256 GPU nodes which have 80 GB of GPU-attached memory instead of 40 GB. To request this, use -C gpu&hbm80g in your job script.
-C gpu&hbm80g
Warn
When requesting nodes with a specific amount of GPU-attached memory (e.g., gpu&hbm80g or gpu&hbm40g ) from the command line, use quotation marks to prevent your shell from interpreting the ampersand as creating a background process:
gpu&hbm80g
gpu&hbm40g
$ salloc -N 1 -q interactive -t 00 :30:00 -C gpu & hbm80g -A mxxxx [ 1 ] 1611989 -bash: hbm80g: command not found
$ salloc: error: Job request does not match any supported policy.
salloc: error: Job submit/allocate failed: Unspecified error
$
$ salloc -N 1 -q interactive -t 00 :30:00 -C "gpu&hbm80g" -A mxxxx
salloc: Granted job allocation 26135598 salloc: Waiting for resource configuration
salloc: Nodes nid008284 are ready for job
$ salloc -N 1 -q interactive -t 00 :30:00 -C gpu & hbm80g -A mxxxx [ 1 ] 1611989 -bash: hbm80g: command not found
$ salloc: error: Job request does not match any supported policy.
salloc: error: Job submit/allocate failed: Unspecified error
$
$ salloc -N 1 -q interactive -t 00 :30:00 -C "gpu&hbm80g" -A mxxxx
salloc: Granted job allocation 26135598 salloc: Waiting for resource configuration
salloc: Nodes nid008284 are ready for job
The whole-number argument to the -c flag is inversely proportional to the number of CPU tasks per node.
-c
The value for GPU nodes can be computed with
For example, if you want to run 5 MPI tasks per node, then your argument to the -c flag would be calculated as
-c
The value for CPU-only nodes can be computed with
For details, check the Slurm Options for Perlmutter affinity.

## Explicitly specify GPU resources when requesting GPU nodes ¶

You must explicitly request GPU resources using a SLURM option such as --gpus , --gpus-per-node , or --gpus-per-task to allocate GPU resources for a job. Typically you would add this option in the #SBATCH preamble of your script, e.g., #SBATCH --gpus-per-node=4 .
--gpus
--gpus-per-node
--gpus-per-task
#SBATCH
#SBATCH --gpus-per-node=4
Failing to explicitly request GPU resources may result in output such as the following:
no CUDA-capable device is detected
no CUDA-capable device is detected
No Cuda device found
No Cuda device found

## Implicit GPU binding ¶

The --gpus-per-task option will implicitly set --gpu-bind=per_task:<gpus_per_task> which will restrict GPU access to the tasks which they are bound to. The implicit behavior can be overridden with an explicit --gpu-bind specification such as --gpu-bind=none . For more information on GPU binding on Perlmutter, please see the process affinity section .
--gpus-per-task
--gpu-bind=per_task:<gpus_per_task>
--gpu-bind
--gpu-bind=none

## Oversubscribing GPUs with CUDA Multi-Process Service ¶

The CUDA Multi-Process Service (MPS) enables multiple MPI ranks to concurrently share the resources of a GPU. This can benefit performance when the GPU compute capacity is underutilized by a single application process.
To use MPS, you must start the MPS control daemon in your batch script or in an interactive session:
nvidia-cuda-mps-control -d
nvidia-cuda-mps-control -d
Then, you can launch your application as usual by using an srun command.
srun
To shut down the MPS control daemon and revert back to the default CUDA runtime, run:
echo quit | nvidia-cuda-mps-control
echo quit | nvidia-cuda-mps-control
For multi-node jobs, the MPS control daemon must be started on each node before running your application. One way to accomplish this is to use a wrapper script inserted after the srun portion of the command:
srun
#!/bin/bash # Example mps-wrapper.sh usage: # > srun [srun args] mps-wrapper.sh [cmd] [cmd args] export CUDA_MPS_PIPE_DIRECTORY = /tmp/nvidia-mps export CUDA_MPS_LOG_DIRECTORY = /tmp/nvidia-log # Launch MPS from a single rank per node if [ $SLURM_LOCALID -eq 0 ] ; then CUDA_VISIBLE_DEVICES = $SLURM_JOB_GPUS nvidia-cuda-mps-control -d fi # Wait for MPS to start sleep 5 # Run the command " $@ " # Quit MPS control daemon before exiting if [ $SLURM_LOCALID -eq 0 ] ; then echo quit | nvidia-cuda-mps-control fi
#!/bin/bash # Example mps-wrapper.sh usage: # > srun [srun args] mps-wrapper.sh [cmd] [cmd args] export CUDA_MPS_PIPE_DIRECTORY = /tmp/nvidia-mps export CUDA_MPS_LOG_DIRECTORY = /tmp/nvidia-log # Launch MPS from a single rank per node if [ $SLURM_LOCALID -eq 0 ] ; then CUDA_VISIBLE_DEVICES = $SLURM_JOB_GPUS nvidia-cuda-mps-control -d fi # Wait for MPS to start sleep 5 # Run the command " $@ " # Quit MPS control daemon before exiting if [ $SLURM_LOCALID -eq 0 ] ; then echo quit | nvidia-cuda-mps-control fi
For this wrapper script to work, all GPUs per node must be visible to node local rank 0 so it is unlikely to work in conjunction with Slurm options that restrict access to GPUs such as --gpu-bind=map_gpu or --gpus-per-task . See the GPU affinity settings section for alternative methods to map GPUs to MPI tasks.
--gpu-bind=map_gpu
--gpus-per-task
For more information about CUDA Multi-Process Service, see:
NVIDIA's CUDA MPS Documentation
MPS training hosted by NERSC, Aug 2021

## Example scripts ¶

Tip
The below examples use a code called ./gpus_for_tasks . To build ./gpus_for_tasks for yourself, see the code and commands in the GPU affinity settings section.
./gpus_for_tasks
./gpus_for_tasks

## 1 node, 1 task, 1 GPU ¶

Tip
Jobs using 1 or 2 GPUs should request the shared QOS.
shared
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q shared #SBATCH -t 1:00:00 #SBATCH -n 1 #SBATCH -c 32 #SBATCH --gpus-per-task=1 export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q shared #SBATCH -t 1:00:00 #SBATCH -n 1 #SBATCH -c 32 #SBATCH --gpus-per-task=1 export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
Output:
Rank 0 out of 1 processes: I see 1 GPU(s). 0 for rank 0: 0000:03:00.0
Rank 0 out of 1 processes: I see 1 GPU(s). 0 for rank 0: 0000:03:00.0

## 1 node, 4 tasks, 4 GPUs, all GPUs visible to all tasks ¶

#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 1 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 #SBATCH --gpu-bind=none export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 1 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 #SBATCH --gpu-bind=none export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
Output:
Rank 1 out of 4 processes: I see 4 GPU(s).
0 for rank 1: 0000:03:00.0
1 for rank 1: 0000:41:00.0
2 for rank 1: 0000:81:00.0
3 for rank 1: 0000:C1:00.0
Rank 2 out of 4 processes: I see 4 GPU(s).
0 for rank 2: 0000:03:00.0
1 for rank 2: 0000:41:00.0
2 for rank 2: 0000:81:00.0
3 for rank 2: 0000:C1:00.0
Rank 3 out of 4 processes: I see 4 GPU(s).
0 for rank 3: 0000:03:00.0
1 for rank 3: 0000:41:00.0
2 for rank 3: 0000:81:00.0
3 for rank 3: 0000:C1:00.0
Rank 0 out of 4 processes: I see 4 GPU(s).
0 for rank 0: 0000:03:00.0
1 for rank 0: 0000:41:00.0
2 for rank 0: 0000:81:00.0
3 for rank 0: 0000:C1:00.0
Rank 1 out of 4 processes: I see 4 GPU(s).
0 for rank 1: 0000:03:00.0
1 for rank 1: 0000:41:00.0
2 for rank 1: 0000:81:00.0
3 for rank 1: 0000:C1:00.0
Rank 2 out of 4 processes: I see 4 GPU(s).
0 for rank 2: 0000:03:00.0
1 for rank 2: 0000:41:00.0
2 for rank 2: 0000:81:00.0
3 for rank 2: 0000:C1:00.0
Rank 3 out of 4 processes: I see 4 GPU(s).
0 for rank 3: 0000:03:00.0
1 for rank 3: 0000:41:00.0
2 for rank 3: 0000:81:00.0
3 for rank 3: 0000:C1:00.0
Rank 0 out of 4 processes: I see 4 GPU(s).
0 for rank 0: 0000:03:00.0
1 for rank 0: 0000:41:00.0
2 for rank 0: 0000:81:00.0
3 for rank 0: 0000:C1:00.0

## 1 node, 4 tasks, 4 GPUs, 1 GPU visible to each task ¶

#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 1 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 1 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
Output:
Rank 1 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 1 : 0000 :41:00.0
Rank 2 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 2 : 0000 :81:00.0
Rank 0 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 0 : 0000 :03:00.0
Rank 3 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 3 : 0000 :C1:00.0
Rank 1 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 1 : 0000 :41:00.0
Rank 2 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 2 : 0000 :81:00.0
Rank 0 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 0 : 0000 :03:00.0
Rank 3 out of 4 processes: I see 1 GPU ( s ) . 0 for rank 3 : 0000 :C1:00.0

## 4 nodes, 16 tasks, 16 GPUs, all GPUs visible to all tasks ¶

#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 4 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 #SBATCH --gpu-bind=none export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 4 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 #SBATCH --gpu-bind=none export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
Output:
Rank 10 out of 16 processes: I see 4 GPU(s).
0 for rank 10: 0000:03:00.0
1 for rank 10: 0000:41:00.0
2 for rank 10: 0000:81:00.0
3 for rank 10: 0000:C1:00.0
Rank 1 out of 16 processes: I see 4 GPU(s).
0 for rank 1: 0000:03:00.0
1 for rank 1: 0000:41:00.0
2 for rank 1: 0000:81:00.0
3 for rank 1: 0000:C1:00.0
Rank 8 out of 16 processes: I see 4 GPU(s).
0 for rank 8: 0000:03:00.0
1 for rank 8: 0000:41:00.0
2 for rank 8: 0000:81:00.0
3 for rank 8: 0000:C1:00.0
Rank 4 out of 16 processes: I see 4 GPU(s).
0 for rank 4: 0000:03:00.0
1 for rank 4: 0000:41:00.0
2 for rank 4: 0000:81:00.0
3 for rank 4: 0000:C1:00.0
Rank 2 out of 16 processes: I see 4 GPU(s).
0 for rank 2: 0000:03:00.0
1 for rank 2: 0000:41:00.0
2 for rank 2: 0000:81:00.0
3 for rank 2: 0000:C1:00.0
Rank 15 out of 16 processes: I see 4 GPU(s).
0 for rank 15: 0000:03:00.0
1 for rank 15: 0000:41:00.0
2 for rank 15: 0000:81:00.0
3 for rank 15: 0000:C1:00.0
Rank 13 out of 16 processes: I see 4 GPU(s).
0 for rank 13: 0000:03:00.0
1 for rank 13: 0000:41:00.0
2 for rank 13: 0000:81:00.0
3 for rank 13: 0000:C1:00.0
Rank 14 out of 16 processes: I see 4 GPU(s).
0 for rank 14: 0000:03:00.0
1 for rank 14: 0000:41:00.0
2 for rank 14: 0000:81:00.0
3 for rank 14: 0000:C1:00.0
Rank 5 out of 16 processes: I see 4 GPU(s).
0 for rank 5: 0000:03:00.0
1 for rank 5: 0000:41:00.0
2 for rank 5: 0000:81:00.0
3 for rank 5: 0000:C1:00.0
Rank 6 out of 16 processes: I see 4 GPU(s).
0 for rank 6: 0000:03:00.0
1 for rank 6: 0000:41:00.0
2 for rank 6: 0000:81:00.0
3 for rank 6: 0000:C1:00.0
Rank 7 out of 16 processes: I see 4 GPU(s).
0 for rank 7: 0000:03:00.0
1 for rank 7: 0000:41:00.0
2 for rank 7: 0000:81:00.0
3 for rank 7: 0000:C1:00.0
Rank 3 out of 16 processes: I see 4 GPU(s).
0 for rank 3: 0000:03:00.0
1 for rank 3: 0000:41:00.0
2 for rank 3: 0000:81:00.0
3 for rank 3: 0000:C1:00.0
Rank 0 out of 16 processes: I see 4 GPU(s).
0 for rank 0: 0000:03:00.0
1 for rank 0: 0000:41:00.0
2 for rank 0: 0000:81:00.0
3 for rank 0: 0000:C1:00.0
Rank 11 out of 16 processes: I see 4 GPU(s).
0 for rank 11: 0000:03:00.0
1 for rank 11: 0000:41:00.0
2 for rank 11: 0000:81:00.0
3 for rank 11: 0000:C1:00.0
Rank 9 out of 16 processes: I see 4 GPU(s).
0 for rank 9: 0000:03:00.0
1 for rank 9: 0000:41:00.0
2 for rank 9: 0000:81:00.0
3 for rank 9: 0000:C1:00.0
Rank 12 out of 16 processes: I see 4 GPU(s).
0 for rank 12: 0000:03:00.0
1 for rank 12: 0000:41:00.0
2 for rank 12: 0000:81:00.0
3 for rank 12: 0000:C1:00.0
Rank 10 out of 16 processes: I see 4 GPU(s).
0 for rank 10: 0000:03:00.0
1 for rank 10: 0000:41:00.0
2 for rank 10: 0000:81:00.0
3 for rank 10: 0000:C1:00.0
Rank 1 out of 16 processes: I see 4 GPU(s).
0 for rank 1: 0000:03:00.0
1 for rank 1: 0000:41:00.0
2 for rank 1: 0000:81:00.0
3 for rank 1: 0000:C1:00.0
Rank 8 out of 16 processes: I see 4 GPU(s).
0 for rank 8: 0000:03:00.0
1 for rank 8: 0000:41:00.0
2 for rank 8: 0000:81:00.0
3 for rank 8: 0000:C1:00.0
Rank 4 out of 16 processes: I see 4 GPU(s).
0 for rank 4: 0000:03:00.0
1 for rank 4: 0000:41:00.0
2 for rank 4: 0000:81:00.0
3 for rank 4: 0000:C1:00.0
Rank 2 out of 16 processes: I see 4 GPU(s).
0 for rank 2: 0000:03:00.0
1 for rank 2: 0000:41:00.0
2 for rank 2: 0000:81:00.0
3 for rank 2: 0000:C1:00.0
Rank 15 out of 16 processes: I see 4 GPU(s).
0 for rank 15: 0000:03:00.0
1 for rank 15: 0000:41:00.0
2 for rank 15: 0000:81:00.0
3 for rank 15: 0000:C1:00.0
Rank 13 out of 16 processes: I see 4 GPU(s).
0 for rank 13: 0000:03:00.0
1 for rank 13: 0000:41:00.0
2 for rank 13: 0000:81:00.0
3 for rank 13: 0000:C1:00.0
Rank 14 out of 16 processes: I see 4 GPU(s).
0 for rank 14: 0000:03:00.0
1 for rank 14: 0000:41:00.0
2 for rank 14: 0000:81:00.0
3 for rank 14: 0000:C1:00.0
Rank 5 out of 16 processes: I see 4 GPU(s).
0 for rank 5: 0000:03:00.0
1 for rank 5: 0000:41:00.0
2 for rank 5: 0000:81:00.0
3 for rank 5: 0000:C1:00.0
Rank 6 out of 16 processes: I see 4 GPU(s).
0 for rank 6: 0000:03:00.0
1 for rank 6: 0000:41:00.0
2 for rank 6: 0000:81:00.0
3 for rank 6: 0000:C1:00.0
Rank 7 out of 16 processes: I see 4 GPU(s).
0 for rank 7: 0000:03:00.0
1 for rank 7: 0000:41:00.0
2 for rank 7: 0000:81:00.0
3 for rank 7: 0000:C1:00.0
Rank 3 out of 16 processes: I see 4 GPU(s).
0 for rank 3: 0000:03:00.0
1 for rank 3: 0000:41:00.0
2 for rank 3: 0000:81:00.0
3 for rank 3: 0000:C1:00.0
Rank 0 out of 16 processes: I see 4 GPU(s).
0 for rank 0: 0000:03:00.0
1 for rank 0: 0000:41:00.0
2 for rank 0: 0000:81:00.0
3 for rank 0: 0000:C1:00.0
Rank 11 out of 16 processes: I see 4 GPU(s).
0 for rank 11: 0000:03:00.0
1 for rank 11: 0000:41:00.0
2 for rank 11: 0000:81:00.0
3 for rank 11: 0000:C1:00.0
Rank 9 out of 16 processes: I see 4 GPU(s).
0 for rank 9: 0000:03:00.0
1 for rank 9: 0000:41:00.0
2 for rank 9: 0000:81:00.0
3 for rank 9: 0000:C1:00.0
Rank 12 out of 16 processes: I see 4 GPU(s).
0 for rank 12: 0000:03:00.0
1 for rank 12: 0000:41:00.0
2 for rank 12: 0000:81:00.0
3 for rank 12: 0000:C1:00.0

## 4 nodes, 16 tasks, 16 GPUs, 1 GPU visible to each task ¶

#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 4 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -q regular #SBATCH -t 1:00:00 #SBATCH -N 4 #SBATCH --ntasks-per-node=4 #SBATCH -c 32 #SBATCH --gpus-per-task=1 export SLURM_CPU_BIND = "cores" srun ./gpus_for_tasks
Output:
Rank 15 out of 16 processes: I see 1 GPU(s).
0 for rank 15: 0000:C1:00.0
Rank 14 out of 16 processes: I see 1 GPU(s).
0 for rank 14: 0000:81:00.0
Rank 13 out of 16 processes: I see 1 GPU(s).
0 for rank 13: 0000:41:00.0
Rank 1 out of 16 processes: I see 1 GPU(s).
0 for rank 1: 0000:41:00.0
Rank 9 out of 16 processes: I see 1 GPU(s).
0 for rank 9: 0000:41:00.0
Rank 12 out of 16 processes: I see 1 GPU(s).
0 for rank 12: 0000:03:00.0
Rank 5 out of 16 processes: I see 1 GPU(s).
0 for rank 5: 0000:41:00.0
Rank 3 out of 16 processes: I see 1 GPU(s).
0 for rank 3: 0000:C1:00.0
Rank 10 out of 16 processes: I see 1 GPU(s).
0 for rank 10: 0000:81:00.0
Rank 6 out of 16 processes: I see 1 GPU(s).
0 for rank 6: 0000:81:00.0
Rank 2 out of 16 processes: I see 1 GPU(s).
0 for rank 2: 0000:81:00.0
Rank 11 out of 16 processes: I see 1 GPU(s).
0 for rank 11: 0000:C1:00.0
Rank 7 out of 16 processes: I see 1 GPU(s).
0 for rank 7: 0000:C1:00.0
Rank 0 out of 16 processes: I see 1 GPU(s).
0 for rank 0: 0000:03:00.0
Rank 8 out of 16 processes: I see 1 GPU(s).
0 for rank 8: 0000:03:00.0
Rank 4 out of 16 processes: I see 1 GPU(s).
0 for rank 4: 0000:03:00.0
Rank 15 out of 16 processes: I see 1 GPU(s).
0 for rank 15: 0000:C1:00.0
Rank 14 out of 16 processes: I see 1 GPU(s).
0 for rank 14: 0000:81:00.0
Rank 13 out of 16 processes: I see 1 GPU(s).
0 for rank 13: 0000:41:00.0
Rank 1 out of 16 processes: I see 1 GPU(s).
0 for rank 1: 0000:41:00.0
Rank 9 out of 16 processes: I see 1 GPU(s).
0 for rank 9: 0000:41:00.0
Rank 12 out of 16 processes: I see 1 GPU(s).
0 for rank 12: 0000:03:00.0
Rank 5 out of 16 processes: I see 1 GPU(s).
0 for rank 5: 0000:41:00.0
Rank 3 out of 16 processes: I see 1 GPU(s).
0 for rank 3: 0000:C1:00.0
Rank 10 out of 16 processes: I see 1 GPU(s).
0 for rank 10: 0000:81:00.0
Rank 6 out of 16 processes: I see 1 GPU(s).
0 for rank 6: 0000:81:00.0
Rank 2 out of 16 processes: I see 1 GPU(s).
0 for rank 2: 0000:81:00.0
Rank 11 out of 16 processes: I see 1 GPU(s).
0 for rank 11: 0000:C1:00.0
Rank 7 out of 16 processes: I see 1 GPU(s).
0 for rank 7: 0000:C1:00.0
Rank 0 out of 16 processes: I see 1 GPU(s).
0 for rank 0: 0000:03:00.0
Rank 8 out of 16 processes: I see 1 GPU(s).
0 for rank 8: 0000:03:00.0
Rank 4 out of 16 processes: I see 1 GPU(s).
0 for rank 4: 0000:03:00.0

## Single-GPU tasks in parallel ¶

Users who have many independent single-GPU tasks may wish to pack these into one job which runs the tasks in parallel on different GPUs. There are multiple ways to accomplish this; here we present one example.
srun
srun
The Slurm srun command can be used to launch individual tasks, each allocated some amount of resources requested by the job script. An example of this is:
srun
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -N 1 #SBATCH -t 5 #SBATCH --ntasks-per-node=4 srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & wait
#!/bin/bash #SBATCH -A <account> #SBATCH -C gpu #SBATCH -N 1 #SBATCH -t 5 #SBATCH --ntasks-per-node=4 srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & srun --exact -u -n 1 --gpus-per-task 1 -c 1 --mem-per-cpu = 4G bash -c 'date +%M:%S; sleep 15; date +%M:%S' & wait
Output shows all steps started at the same time:
23:12
23:12
23:12
23:12
23:27
23:27
23:27
23:27
23:12
23:12
23:12
23:12
23:27
23:27
23:27
23:27
Each srun invocation requests one task and one GPU for that task. Specifying --exact will allow the steps to be launched in parallel if the rest of the resources still fit on the node. Hence, it is necessary to also specify memory and cpu usage with -c 1 --mem-per-cpu=4G as otherwise each step would claim all cpus and memory (the default) which would cause the steps to wait for each other to free up resources. If these 4 tasks are all you wish to run on that node, you can specify more memory and cpus per task/gpu, e.g. -c 32 --mem-per-gpu=55G would split the node's resources into 4 equally sized parts. The & at the end of each line puts the tasks in the background, and the final wait command is needed to allow all of the tasks to run to completion.
srun
--exact
-c 1 --mem-per-cpu=4G
-c 32 --mem-per-gpu=55G
&
wait
Do not use srun for large numbers of tasks
srun
This approach is feasible for relatively small numbers (i.e., tens) of tasks but should not be used for hundreds or thousands of tasks. To run larger numbers of tasks, GNU Parallel is preferred.

## MPI applications on CPU-only nodes ¶

The following job script is to run an MPI application on CPU-only nodes. 32 MPI tasks will be launched over 2 CPU-only nodes, so each node will have 16 MPI tasks. The -c value is set to 2\times\left \lfloor{\frac{128}{16}}\right \rfloor = 16 .
-c
For the <account> name below, use a CPU allocation account (that is, the one without the trailing _g ).
<account>
_g
#!/bin/bash #SBATCH -A <account> #SBATCH -C cpu #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=2 #SBATCH --ntasks-per-node=16 srun -n 32 --cpu-bind = cores -c 16 ./myapp
#!/bin/bash #SBATCH -A <account> #SBATCH -C cpu #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=2 #SBATCH --ntasks-per-node=16 srun -n 32 --cpu-bind = cores -c 16 ./myapp
Users are encouraged to check many CPU job script examples in the Example job scripts page.