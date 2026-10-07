---
name: perlmutter-slurm-job-submission
description: Instructions for running interactive, batch, and data transfer jobs on Perlmutter using the Slurm workload manager.
created: 2026-10-07T03:35:26.109061+00:00
updated: 2026-10-07T03:35:26.109061+00:00
---

## Question
How to run a job in perlmutter?

## Answer
To run a job on Perlmutter, you use the **Slurm** workload manager. Depending on your needs, you can run a command interactively, submit a batch script, or use a wrapper for single commands.

### 1. Run a Simple Command (Interactive/Quick)
Use `srun` for quick tests or simple commands.
*   **CPU Node (Debug QOS):**
    ```bash
    srun --constraint=cpu --ntasks=1 --time 5 --qos debug hostname
    ```
*   **GPU Node (Debug QOS):**
    ```bash
    srun --constraint=gpu --ntasks=1 -G 1 --time 5 -A <account> --qos debug nvidia-smi
    ```

### 2. Submit a Batch Job (Using a Script)
For production runs, create a shell script with `#SBATCH` directives and submit it using `sbatch`.

**Example Batch Script:**
```bash
#!/bin/bash
#SBATCH -q regular             # Quality of Service (regular, debug, etc.)
#SBATCH -C cpu                 # Constraint: cpu or gpu
#SBATCH -N 1                   # Number of nodes
#SBATCH -n 16                  # Total number of tasks
#SBATCH -t 00:20:00            # Time limit (HH:MM:SS)
#SBATCH --job-name=my_job      # Name of the job

# Your commands here
./my_program
```
**Submission command:**
```bash
sbatch my_script.sh
```

### 3. Submit a Command Without a Script
You can use the `--wrap` option with `sbatch` to run a single command as a batch job:
```bash
sbatch --constraint=gpu --ntasks=1 -G 1 --time 5 -A <account> --qos debug --wrap="nvidia-smi"
```

### 4. Special Case: Data Transfer (Xfer QOS)
To transfer data between compute systems and the HPSS archive, use the `xfer` QOS. These jobs run on login nodes and are free of charge.
*   **Command line:** `sbatch -q xfer -C cron hsi put <my_files>`
*   **Note:** Do not run computational jobs in the `xfer` QOS.

### Summary of Slurm Tools
| Tool | Use Case |
| :--- | :--- |
| `srun` | Quick interactive tasks or simple commands. |
| `sbatch` | Submitting background batch scripts for longer runs. |
| `squeue` | Monitoring the status of your submitted jobs. |
| `scancel` | Cancelling a running or pending job (e.g., `scancel $JobID`). |
| `sacct` | Reporting accounting information for active or completed jobs. |

*(Source: muller-perlmutter-job-submission)*

## Approach
- What was missing: The specific Slurm commands, QOS options, and script templates required for Perlmutter CPU and GPU nodes.
- Where I looked: I used `list_notes` with the query "run a job in perlmutter".
- What I found: The note `muller-perlmutter-job-submission` contained detailed instructions for `srun`, `sbatch`, and the `xfer` QOS.
- How I built the answer: I synthesized the information from the note into four categories: simple interactive commands, batch script submission, using the `--wrap` option, and data transfer via `xfer` QOS.
- Next time: Go directly to the `muller-perlmutter-job-submission` note for comprehensive Slurm usage on Perlmutter.
