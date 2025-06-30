#!/bin/bash
#SBATCH -C gpu
#SBATCH -G 4
#SBATCH -n 4
#SBATCH -c 32
#SBATCH -q debug
#SBATCH -J vasp-test
#SBATCH -t 00:30:00

# OpenMP settings:
export OMP_NUM_THREADS=1
export OMP_PLACES=threads
export OMP_PROC_BIND=spread

# Load vasp module
module load vasp-tpc/6.4.2-gpu

#cat << jide
#
#$(date)
#
#${SLURM_JOB_NAME}
#
#${SLURM_JOB_ID}
#
#$(hostname)
#
#${SLURM_JOB_NODELIST}
#
#jide

srun -u --cpu-bind=cores --gpu-bind=none vasp_std
