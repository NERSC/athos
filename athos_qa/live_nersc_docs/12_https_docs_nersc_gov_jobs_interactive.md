# Source: https://docs.nersc.gov/jobs/interactive/

## Interactive Jobs ¶


## Allocation ¶

salloc is used to allocate resources in real time to run an interactive batch job. Typically, this is used to allocate resources and spawn a shell. The shell is then used to execute srun commands to launch parallel tasks.
salloc
srun

## "interactive" QOS on Perlmutter ¶

Perlmutter has a dedicated interactive QOS to support medium-length interactive work. This QOS is intended to deliver nodes for interactive use within 6 minutes of the job request.
Warning
On Perlmutter, if you have not set a default account , salloc may fail with the following error message:
salloc: error: Job request does not match any supported policy.
salloc: error: Job submit/allocate failed: Unspecified error
salloc: error: Job request does not match any supported policy.
salloc: error: Job submit/allocate failed: Unspecified error
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint gpu --gpus 4 --account mxxxx
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint gpu --gpus 4 --account mxxxx
When using srun, you must explicitly request for GPU resources
One must use the --gpus ( -G ), --gpus-per-node , or --gpus-per-task flag to make the allocated node's GPUs visible to your srun command.
--gpus
-G
--gpus-per-node
--gpus-per-task
srun
Otherwise, you will see errors / complaints similar to: no CUDA-capable device is detected
no CUDA-capable device is detected
no CUDA-capable device is detected
No Cuda device found
No Cuda device found
When requesting for an interactive node on the Perlmutter GPU compute nodes
One must use the project name that ends in _g (e.g., mxxxx_g) to submit any jobs to run on the Perlmutter GPU nodes. The -C (constraint flag) must also be set to GPUs for any interactive jobs ( -C gpu or --constraint gpu ).
-C gpu
--constraint gpu
Otherwise, you will notice errors such as: sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
sbatch: error: Job request does not match any supported policy.
sbatch: error: Batch job submission failed: Unspecified error
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint cpu --account mxxxx
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint cpu --account mxxxx
If resources are not readily available for the requested interactive job, it is automatically canceled after 6 minutes. To allow a job to wait for resources for a longer time, one can use optional the --immediate flag to specify the number of seconds that the job should wait for available resources:
--immediate
# wait for up to 10 minutes salloc --nodes 1 --qos interactive --time 01 :00:00 --constraint <node type> --account mxxxx --immediate = 600
# wait for up to 10 minutes salloc --nodes 1 --qos interactive --time 01 :00:00 --constraint <node type> --account mxxxx --immediate = 600
There is a maximum node limit of 4 nodes for interactive jobs on both cpu and gpu partitions. For more details see QOS Limits and Charges .
cpu
gpu