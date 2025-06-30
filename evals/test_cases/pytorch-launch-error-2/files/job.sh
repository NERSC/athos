#!/bin/bash
#SBATCH -J torchrun-test
#SBATCH -q debug
#SBATCH -C gpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=32
#SBATCH --time 10

# Environment setup
module load pytorch/2.6.0

# Use scratch for huggingface cache
export HF_HOME=$SCRATCH/cache/huggingface

# Distributed training configuration
export MASTER_ADDR=$(hostname)
export MASTER_PORT=29507

# Other settings
export OMP_NUM_THREADS=8
#export NCCL_DEBUG=INFO

set -x

# Using torchrun
srun -l -u torchrun \
    --nnodes=$SLURM_JOB_NUM_NODES \
    --nproc-per-node=$SLURM_GPUS_PER_NODE \
    --rdzv-backend=c10d \
    --rdzv-endpoint=$MASTER_ADDR:$MASTER_PORT \
    nlp_example.py

echo "SUCCESS"
