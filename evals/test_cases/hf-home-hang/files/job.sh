#!/bin/bash
#SBATCH -J hf-example
#SBATCH -q debug
#SBATCH -C gpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=32
#SBATCH --time 10

# Environment setup
module load pytorch/2.6.0

# Distributed training configuration
export MASTER_ADDR=$(hostname)
export MASTER_PORT=29507

# Other settings
export OMP_NUM_THREADS=8

set -x

srun -l bash -c "
    export RANK=\$SLURM_PROCID
    export LOCAL_RANK=\$SLURM_LOCALID
    export WORLD_SIZE=\$SLURM_NTASKS
    python nlp_example.py
"

echo "SUCCESS"
