In this example, the job script is missing some settings required to
initialize data parallel training, so the communication wireup fails and
the script starts up multiple independent model trainings instead of doing
a single multi-node training.

The fix is to add these lines to the torchrun arguments:

```
    --nnodes=$SLURM_JOB_NUM_NODES \
    --rdzv-backend=c10d \
    --rdzv-endpoint=$MASTER_ADDR:$MASTER_PORT \
```
