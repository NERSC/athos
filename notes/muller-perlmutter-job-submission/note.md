---
name: muller-perlmutter-job-submission
description: Resolve requests for "muller" system jobs by providing Perlmutter Slurm submission instructions.
created: 2026-10-07T03:32:17.833006+00:00
updated: 2026-10-07T03:32:17.833006+00:00
---

## Question
how to run a job in muller?

## Answer
I could not find any references to a system named "muller" in the documentation. However, there is extensive documentation for **Perlmutter**, which is the flagship computing system at NERSC. Assuming you are referring to Perlmutter, here is how to run a job.

Perlmutter uses the **Slurm** workload manager to schedule and run jobs.

### 1. Run a Simple Command (Interactive/Quick)
For quick tests or simple commands without creating a script, use `srun`.

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

### 4. Special Cases: Data Transfer (Xfer QOS)
To transfer data between compute systems and the HPSS archive, use the `xfer` QOS. These jobs run on login nodes and are free of charge.
*   **Command line:** `sbatch -q xfer -C cron hsi put <my_files>`
*   **Note:** Do not run computational jobs in the `xfer` QOS.

### Summary of Tools
| Tool | Use Case |
| :--- | :--- |
| `srun` | Quick interactive tasks or simple commands. |
| `sbatch` | Submitting background batch scripts for longer runs. |
| `squeue` | Monitoring the status of your submitted jobs. |
| `scancel` | Cancelling a running or pending job (e.g., `scancel $JobID`). |
| `sacct` | Reporting accounting information for active or completed jobs. |

*Source: `docs` collection (files: `jobs/examples/index.md`, `getting-started.md`, `jobs/monitoring.md`)*

## Approach
- What was missing: Documentation for a system named "muller".
- Where I looked: First checked `list_notes` (nothing), then identified collections via `chroma_list_collections`, and finally queried the `docs` collection with "how to run a job in muller", "muller job submission", and "muller cluster usage".
- What I found: No results for "muller", but found extensive Perlmutter Slurm documentation in `docs` via `jobs/examples/index.md`, `getting-started.md`, and `jobs/monitoring.md`.
- How I built the answer: Assumed "muller" was a typo for "Perlmutter" and combined information on `srun` for interactive tasks, `sbatch` for batch scripts, the `--wrap` option for single commands, and the `xfer` QOS for data transfers.
- Next time: If a user asks for "muller", treat it as a typo for Perlmutter and search the `docs` collection for Slurm submission guides.
