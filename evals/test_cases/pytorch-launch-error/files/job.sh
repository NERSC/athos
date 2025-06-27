#!/bin/bash
#SBATCH -J torchrun-test
#SBATCH -q debug
#SBATCH -C gpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=128
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

set -x

# Using torchrun
srun -u torchrun \
    --nproc-per-node=$SLURM_GPUS_PER_NODE \
    nlp_example.py

echo "SUCCESS"
