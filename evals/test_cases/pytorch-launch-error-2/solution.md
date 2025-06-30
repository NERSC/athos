The problem in this case is that the job script is launching 4 slurm tasks
per node but also launching 4 training processes per rank with torchrun, which
results in 16 processes per node instead of the intended 4.

One fix is to configure slurm to only launch 1 task per node and have torchrun
launch the 4 ranks per node.
