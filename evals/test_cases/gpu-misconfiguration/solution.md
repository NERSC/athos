The job ran on a CPU node because the sbatch script never requested GPUs. When the PyTorch code tried to initialize CUDA it failed with "no CUDA-capable device is detected." Request a GPU node and GPUs in the script, e.g.

```bash
#SBATCH -C gpu
#SBATCH --gpus-per-node=4   # or --gpus=4 for a single-node job
```
