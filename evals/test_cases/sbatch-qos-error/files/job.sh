#!/bin/bash
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 8:00:00
#SBATCH --gpus-per-node=4
#SBATCH --ntasks-per-node=4
module load pytorch
python train.py
