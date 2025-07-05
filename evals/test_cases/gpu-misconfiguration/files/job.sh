#!/bin/bash
#SBATCH -J pytorch-test
#SBATCH -q regular
#SBATCH -t 10
module load pytorch/2.6.0
python train.py
