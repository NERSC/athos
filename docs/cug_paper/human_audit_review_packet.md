# Human Audit Review Packet

This packet is generated from the audit worksheet and is intended to let a reviewer inspect each sampled case without opening raw `run.json` files manually.

Primary worksheet:
- `docs/cug_paper/human_audit_review_sheet.csv`

Total rows: 48

## 1. lang_gptoss_base | qa | clear_pass | 9b40dfd8d72f

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/nersc_qa.v2/9b40dfd8d72f/0/run.json`

### User Prompt

````text
How does a user load a specific software module on Perlmutter?
````

### Model Answer

````text
**Quick answer:**  
On Perlmutter you use the standard **Lmod** module commands:

```bash
module load <software>/<version>
```

For example, to get Python 3.10 from the Anaconda stack:

```bash
module load python/3.10-anaconda-2022.05
```

---

## Step‑by‑step guide

| Step | What to do | Example command |
|------|------------|-----------------|
| **1. Log in** | SSH to the system | `ssh your‑id@perlmutter.nersc.gov` |
| **2. Find the module you need** | List everything or search for a specific name | `module avail`  (all)  <br> `module spider netcdf` (search) |
| **3. Pick the exact version** | `module spider <name>` shows all available flavors and versions | `module spider netcdf` → shows `netcdf/4.9.2` and `netcdf/4.9.2‑gcc/12.2.0`, etc. |
| **4. Load the module** | Use the full name (software/ version) | `module load netcdf/4.9.2` |
| **5. Verify** | See what’s currently loaded | `module list` |
| **6. Use it** | Run your program, start an interactive session, or put the load line in a batch script | See below for job‑script example |

---

### Commonly used module commands

| Command | Purpose |
|---------|---------|
| `module load <mod>/<ver>` | Load a specific module |
| `module unload <mod>` | Remove a module |
| `module swap <old> <new>` | Replace one module with another |
| `module purge` | Clear **all** loaded modules (good practice at the start of a job script) |
| `module list` | Show what’s currently loaded |
| `module spider <mod>` | Search for a module and view its dependencies |
| `ml <mod>/<ver>` | Shortcut; `ml` is an alias for `module load` |
| `module save <name>` / `module restore <name>` | Snapshot and later restore a whole environment |

---

### Using modules in a Slurm batch script

```bash
#!/bin/bash
#SBATCH -N 1                # number of nodes
#SBATCH -t 00:30:00         # wall‑clock time
#SBATCH -C gpu              # request GPU nodes (or “cpu” for CPU nodes)
#SBATCH -q regular          # queue
#SBATCH -J my_job           # job name

# --- Environment setup -------------------------------------------------
module purge                 # start clean
module load PrgEnv-gnu       # load a programming environment (optional)
module load python/3.10-anaconda-2022.05
module load netcdf/4.9.2
module list                  # optional, just to double‑check

# --- Your actual work ---------------------------------------------------
srun python my_script.py
```

*Place the `module load …` lines **after** the `#SBATCH` directives but **before** any `srun` or executable call.*

---

### Loading modules on an interactive session

If you just need a quick test, you can launch an interactive allocation and load modules inside it:

```bash
srun --pty -t 01:00:00 -C gpu -N 1 bash
# inside the allocation:
module purge
module load python/3.10-anaconda-2022.05
python -c "import sys; print(sys.version)"
```

---

### Tips & gotchas

* **Login nodes are for light work only** – don’t run heavy calculations there; you can still load modules for compiling or data preparation.
* **Version matters** – many modules have multiple builds (e.g., compiled with different compilers). Use `module spider <mod>` to see the exact string you need.
* **Environment persistence** – if you always want a module loaded on login, add the `module load …` line to your `~/.bashrc` (or `~/.zshrc`). Be careful not to overload the login environment; for reproducibility, it’s often better to load modules explicitly in each job script.
* **Conflict handling** – if a module you request conflicts with something already loaded, Lmod will print an error. Use `module swap` or `module purge` first.
* **Documentation** – the most up‑to‑date list of software and versions is on the NERSC docs site: <https://docs.nersc.gov> (search “Perlmutter modules”).

---

**Bottom line:**  
1. `ssh` to Perlmutter.  
2. Find the exact module string with `module spider` or `module avail`.  
3. Load it with `module load <software>/<version>`.  
4. Use `module list` to confirm, and put the same `module load` lines in any batch script you submit.

If you run into a specific module name you can’t find, let me know the software you’re after and I’ll help you locate the exact module string! Happy computing on Perlmutter!
````

### Reference Answer

Answer: Use `module load <modulename>` to load a software module.

Source doc: https://docs.nersc.gov/software/modules/

Section: Modules

Source passage: Load a module with module load <modulename>.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional helpful information.
````

---

## 2. lang_gptoss_base | qa | borderline | 03d9beacf0e4

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/nersc_qa.v2/03d9beacf0e4/0/run.json`

### User Prompt

````text
What environment variable points to a user's home directory at NERSC?
````

### Model Answer

````text
On NERSC the standard Unix environment variable **`$HOME`** points to your home directory (e.g. `/global/homes/your‑username`). You can check it with:

```bash
echo $HOME
```
````

### Reference Answer

Answer: The environment variable $HOME references the user's home directory.

Source doc: https://docs.nersc.gov/filesystems/

Section: Home

Source passage: Permanent, relatively small storage for files such as source code or shell scripts. Referenced by the environment variable $HOME.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response is accurate and more detailed than the reference solution. It provides additional context and an example relevant to NERSC systems, making it more informative but not a perfect match to the concise reference solution.
````

---

## 3. lang_gptoss_base | qa | fail_or_skip | 0481a3b31f19

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/nersc_qa.v2/0481a3b31f19/0/run.json`

### User Prompt

````text
Why is the Home filesystem not recommended for storing conda environments or large software stacks?
````

### Model Answer

````text
**Short answer:**  
The home filesystem on most shared‑cluster or cloud machines is usually **small, quota‑limited, backed‑up, and backed by a relatively slow network file system (NFS, Lustre / GPFS leaf, etc.)**. Conda environments and big software stacks consist of **thousands of small files and often many gigabytes of data**, which makes them a poor fit for that kind of storage. Using $HOME for them can:

| Issue | What happens | Why it matters |
|------|--------------|----------------|
| **Size/Quota limits** | Home directories are often capped at a few GB–tens of GB per user. A full conda environment (especially with many packages or deep dependency trees) can easily exceed that. | Your job may fail mid‑run or you may be forced to delete things to stay under quota. |
| **Performance** | NFS‑style home filesystems have high latency and limited metadata throughput. Conda creates/reads many small files (metadata, binaries, `site‑packages`, etc.). | Environment activation, package install, and even running programs become sluggish. |
| **Backup/IO load** | Home directories are frequently included in regular backups. Large, constantly‑changing envs increase backup size and time, and may cause backup failures. | You waste backup resources and risk hitting backup quotas or causing other users’ backups to fall behind. |
| **Duplication across users** | If each user installs the same large stack in their home, you end up storing the same files many times. | Wasted storage on a shared filesystem that could be used for other projects. |
| **Reliability** | Some clusters purge inactive home files after a period, or place home on a tier that is less fault‑tolerant. | Your environment could disappear unexpectedly. |

---

## How to store conda environments safely and efficiently

| Recommended location | Typical characteristics | Use case |
|----------------------|--------------------------|----------|
| **Project / shared work directory** (e.g., `/project/<proj>/conda_envs`, `/shared/conda`) | Large quota, fast parallel FS (Lustre, GPFS, SSD‑backed). Often read‑only for others, read‑write for the team. | Environments that are reused by many users in the same project. |
| **Scratch / temporary space** (e.g., `$SCRATCH/conda_envs`) | Very fast, large, but may be purged after a set time. | Short‑lived or experimental environments. |
| **Local SSD on compute nodes** (e.g., `$TMPDIR/conda`) | Extremely fast I/O, but limited size and only visible while the node is allocated. | Build‑once, use‐once patterns (e.g., make a tarball of the env, copy to `$TMPDIR`, run, then delete). |
| **Container images** (Docker, Singularity, Apptainer) | Encapsulate the whole stack; no per‑user filesystem churn. | Reproducible runs on any node without installing conda each time. |

### Quick tricks to move an environment off your home

```bash
# 1. Create the target directory (example: project space)
mkdir -p /project/myproj/conda_envs
# 2. Tell conda to look there for new envs
conda config --add envs_dirs /project/myproj/conda_envs
# 3. Optionally, create the env directly in that location
conda create -p /project/myproj/conda_envs/myenv python=3.11
# 4. Activate as usual
conda activate /project/myproj/conda_envs/myenv
```

You can also set `CONDA_ENVS_DIRS` and `CONDA_PKGS_DIRS` environment variables in your job script:

```bash
export CONDA_ENVS_DIRS=/project/myproj/conda_envs
export CONDA_PKGS_DIRS=/project/myproj/conda_pkgs   # for package caches
```

That way all `conda install` commands write to the fast shared area instead of `$HOME/.conda`.

---

## TL;DR Checklist

- **Avoid**: `$HOME/.conda`, `$HOME/miniconda`, `$HOME/.local` for big envs.
- **Prefer**: a directory on a large, high‑performance filesystem (project, scratch, or a dedicated SSD pool).
- **Set**: `conda config --add envs_dirs <path>` or export `CONDA_ENVS_DIRS` to point there.
- **Consider**: containers (Apptainer/Singularity) if you need full reproducibility across nodes.

If you have a specific cluster’s filesystem layout (e.g., “/home is NFS, /project is Lustre”), let me know and I can tailor the exact path and commands for you!
````

### Reference Answer

Answer: Home is not tuned for high-performance parallel jobs. Common should be used for applications sourced by more than a dozen nodes, or software stacks with many small files like conda environments.

Source doc: https://docs.nersc.gov/filesystems/

Section: Home

Source passage: This file system is not tuned for high performance on parallel jobs: use the more optimized Common file system to store applications that need to be sourced by more than a dozen nodes at a time, or applications composed of several packages and small files such as conda environments.

### Automated Judgment

- Status: `scored`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
The agent's response is a detailed explanation that does not match the expected simple statement.
````

---

## 4. lang_gptoss_base | ticket | clear_pass | INC0243653_srun_required_ports_in_use

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/ticket_cases/INC0243653_srun_required_ports_in_use/0/run.json`

### User Prompt

````text
I am submitting a batch workflow that launches many `srun` tasks, and some array tasks fail with messages like:

`srun: Job <jobid> step creation temporarily disabled, retrying (Required ports are in use)`
`srun: Job <jobid> step creation still disabled, retrying (Required ports are in use)`

This does not happen for every task, but it recurs when multiple `srun` commands are active in parallel.

What is the likely cause and how should I change my script to avoid these failures?
````

### Model Answer

````text
**What’s happening?**  
` srun ` creates a *Slurm job step* each time it is invoked.  
When a step is started the `slurmd` daemon on every compute node opens a
TCP port that is used for step‑to‑step I/O forwarding (stdin/stdout,
signal handling, etc.).  The ports are taken from a small range that is
defined in `slurm.conf` (the *step‑port range* – often only a few ports
per node).  

If you launch many `srun` commands in parallel (e.g. dozens of background
`srun … &` inside an array job, or a script that forks off a new step for
each file to process), the per‑node port pool is exhausted.  Slurmd can
no longer allocate a free port, so it disables step creation and you see

```
srun: Job <id> step creation temporarily disabled, retrying (Required ports are in use)
```

The error appears only for the steps that start after the pool is full,
which is why it is intermittent and correlated with the amount of
concurrent `srun` activity.

---

### How to avoid it

#### 1. Reduce the number of concurrent steps *in the script*

| Situation | Typical fix |
|-----------|--------------|
| You have a loop that does `srun … &` for every entry | Limit the concurrency.  Example: |
| |```bash
max_jobs=12                 # or any number that fits the node’s port range
i=0
for file in *.dat; do
    ((i=i%max_jobs)); ((i==0)) && wait   # wait for a “slot” to free
    srun myprog "$file" &                # one step per file
    ((i++))
done
wait
``` |
| You are using a job array but each array element also starts many `srun`s | Use the `%N` array‑limit to throttle the array itself, e.g. `#SBATCH --array=1-500%30`.  Fewer array tasks running at the same time means fewer background steps per node. |
| You need to run a large number of independent tasks | **Don’t spawn a new step for each task.**  Use one of the following instead: |
| | • `srun --ntasks=$SLURM_NTASKS myprog` – run all tasks in a *single* step; Slurm’s internal launch handles the distribution. |
| | • `srun --multi-prog progfile` – a single step that runs many commands listed in a “progfile”. |
| | • A job array *instead of* a loop of `srun`s (`sbatch --array=…`). |
| | • GNU parallel/`xargs -P` **without** wrapping each command in `srun`; the resources are already allocated to the job, so you can start local processes directly. |

#### 2. (If you really need many simultaneous steps) Ask the admin to enlarge the step‑port pool

* In `slurm.conf` add or increase the range, e.g.

```conf
# Reserve a larger range of ports for step‑creation traffic
StepPort=12000-13000        # any unused high‑port range (size ≈ #ports needed × #nodes)
```

* Restart `slurmctld` and `slurmd` after the change.

> **Note:** `StepPort` (older releases used `TaskPort`) is the option that
> controls the ports used by `slurmd` for step I/O.  Raising the range
> gives the daemon more ports to allocate before it hits the “required
> ports are in use” condition.

#### 3. Verify the fix

* Run a small test job that launches the same number of `srun`s you expect.
* If the job finishes without the “step creation temporarily disabled” message,
  the problem is solved.

---

### TL;DR

The error is caused by **port exhaustion on the compute nodes** because the
script launches **too many `srun` steps in parallel**.  Fix it by

1. **Limiting parallel `srun` calls** (use a concurrency limiter in the
   script, or throttle the SLURM array with `%N`), or
2. **Re‑architecting the workflow** so that you run a **single step** that
   contains all tasks (e.g., one `srun` with `--ntasks`/`--multi-prog`,
   or a proper SLURM job array), and/or
3. **Ask the system administrator** to increase the `StepPort` (or `TaskPort`)
   range in `slurm.conf` if you truly need many simultaneous steps.

Implement one of the script‑side changes first; it usually eliminates the
problem without touching the cluster configuration.  If you still hit
the limit, a larger `StepPort` range is the next step. Happy computing!
````

### Reference Answer

Most likely cause: too many concurrent Slurm step launches (`srun`) are contending for step-launch resources/ports, causing transient step creation failures.

Key clues:
- Error explicitly reports `Required ports are in use`.
- Failures appear intermittently across array tasks rather than a deterministic code crash.
- Pattern is associated with launching multiple `srun` steps in parallel.

Correct guidance:
- Reduce simultaneous `srun` launches (serialize some steps, or use fewer concurrent task launches).
- Avoid nested or bursty `srun` invocation patterns inside tight loops where possible.
- If parallel step launching is required, throttle launch rate and monitor with smaller test arrays first.
- Share the job script and failing job IDs with support if issues persist after concurrency reduction.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution, providing a detailed explanation of the issue and offering multiple solutions to resolve it.
````

---

## 5. lang_gptoss_base | ticket | borderline | INC0247918_premium_qos

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/ticket_cases/INC0247918_premium_qos/0/run.json`

### User Prompt

````text
I’m trying to submit Perlmutter jobs under allocation m3560 with premium QOS, but I get:

sbatch: error: Batch job submission failed: Unknown QOS specified

My PI added me to premium access earlier today (about 30–45 minutes ago), but premium still doesn’t appear in Iris for me yet.
Is there anything else I need to do, or is this a NERSC-side issue?
````

### Model Answer

````text
Hey there! 👋  

It looks like the **premium QOS** isn’t visible to you yet, which is why `sbatch` is complaining. This is a common timing issue when a new QOS is added to an allocation.

### Why you see the “Unknown QOS specified” error
* When a PI adds a QOS to an allocation, the change has to propagate through NERSC’s account‑management databases and the Slurm daemons on the system.  
* That propagation can take **anywhere from ~30 minutes up to 2 – 4 hours** (sometimes a bit longer on the very first rollout). Until it finishes, the QOS won’t be listed in Iris, nor will Slurm recognize it.

### Quick things you can check right now

| Command | What it tells you |
|--------|-------------------|
| `sacctmgr list qos format=Name,Default` | Does “premium” appear in the system QOS list? |
| `sacctmgr show assoc where user=$USER format=User,Account,Partition,QOS` | Shows which QOSs are attached to *your* account(s). |
| `scontrol show config | grep QOS` | Confirms that the Slurm controller knows about the QOS. |
| `squeue -O "JobID,User,Partition,QOS"` | If you have any running jobs, you can see which QOS they’re using. |

If `premium` is missing from any of those outputs, the change simply hasn’t propagated yet.

### What to do while you wait
1. **Give it a bit more time** – most users see the QOS appear in Iris and in `sacctmgr` within a couple of hours.  
2. **Verify your allocation name** – make sure you’re using the right `--account` (or `-A`) flag, e.g.:
   ```bash
   sbatch -A m3560 -p gpu --qos=premium my_script.sh
   ```
3. **Avoid “quick retries”** – repeatedly aborting and re‑submitting won’t speed up the propagation; it just creates extra log noise.

### If it’s still missing after ~4 hours
* **Open a NERSC support ticket** – include:  
  * Your NERSC username  
  * Project/Allocation ID (`m3560`)  
  * The QOS you’re trying to use (`premium`)  
  * Approximate time when your PI added the QOS  
* You can also drop a line to **help@nersc.gov** or use the “Contact Support” button in Iris.

### In the meantime …  
If you just need to get a job running while you wait, you can:
* Use the default QOS (`normal`) which is already active for your allocation, **or**
* Ask your PI if it’s okay to submit a short test job under the regular QOS, then switch to premium once it’s live.

---

**Bottom line:** It’s most likely a propagation delay on NERSC’s side. Give it a few more hours, double‑check with the `sacctmgr` commands above, and if the QOS still doesn’t show up, fire off a support ticket.  

Let me know if you’d like help running any of those commands or drafting a support request! 😊
````

### Reference Answer

This is most likely a permission propagation delay, not a job-script syntax issue.

In the ticket, support verified the PI had already granted premium access, and the user started testing shortly after that change. QOS/account permission changes can take time to propagate to Iris/Slurm (on the order of up to about 1 hour).

Correct guidance:
- Confirm PI/proxy grant was completed.
- Wait for propagation, then retry.
- If still failing after the propagation window, escalate with allocation name, timestamp of grant, and exact `sbatch` error.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response correctly identifies the issue as a propagation delay and provides useful troubleshooting steps. However, it differs from the reference solution in the expected propagation time and some details of the guidance. Overall, it is a helpful response but not a perfect match to the expected solution.
````

---

## 6. lang_gptoss_base | ticket | fail_or_skip | INC0242692_multinode_ofi_fix

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/ticket_cases/INC0242692_multinode_ofi_fix/0/run.json`

### User Prompt

````text
An MPI job runs on 1 CPU node but fails on 2+ nodes with:

`open_fabric(...): OFI fi_getinfo() failed (...: No data available)`

What is the likely fix?
````

### Model Answer

````text
The message is coming from Open MPI’s **OFI (libfabric) BTL** – `fi_getinfo()` can’t find any fabric provider that matches the hints it built for inter‑node traffic.  
On a single node the BTL falls back to shared‑memory and works, but as soon as you span more than one node it needs a network provider (InfiniBand, Ethernet, Omni‑Path, …) and fails.

**Typical fix**

1. **Install / load the libfabric provider that matches your interconnect**  
   * InfiniBand → `libfabric‑verbs` (or `libfabric‑ibv`)  
   * Ethernet → `libfabric‑tcp`  
   * Intel Omni‑Path → `libfabric‑psm3` (or `psm2`)  

   On most clusters this is just a module load, e.g.

   ```bash
   module load libfabric
   module load libfabric-ibv   # or libfabric-tcp, libfabric-psm3, …
   ```

2. **Tell libfabric which provider to use** (or let Open MPI pick it)

   ```bash
   export FI_PROVIDER=verbs   # InfiniBand
   # or
   export FI_PROVIDER=tcp     # Ethernet
   # or
   export FI_PROVIDER=psm3    # Omni‑Path
   ```

   You can also set it on the `mpirun` line:

   ```bash
   mpirun -mca btl_ofi_provider_include verbs  …
   ```

3. **If you don’t have any OFI‑compatible fabric** (or just want to fall back to the classic TCP BTL), disable the OFI BTL:

   ```bash
   mpirun -mca btl ^ofi  …
   ```

   This makes Open MPI use `tcp,self,sm` instead of libfabric.

**Why this works** – With the correct provider present (or the OFI BTL disabled) `fi_getinfo()` succeeds, so the MPI job can establish inter‑node connections.

So, in short: *install/load the proper libfabric provider for your network and set `FI_PROVIDER` (or disable the OFI BTL if you don’t need it).*
````

### Reference Answer

Most likely cause: old MPICH/libfabric compatibility break after Slingshot update.

Key clues:
- Failure appears only in multi-node OFI path.
- Known issue tied to older `cray-mpich` versions.

Correct guidance:
- Rebuild with newer `cray-mpich` (for example 8.1.30).
- Temporary workaround: load `libfabric/temp-workaround` if available.
- Migrate to updated toolchain for durable fix.

### Automated Judgment

- Status: `scored`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
The agent's response does not address the specific issue related to MPICH/libfabric compatibility break after Slingshot update. It provides a generic troubleshooting guide for Open MPI, which is a different MPI implementation.
````

---

## 7. lang_sonnet_base | qa | clear_pass | 2e0cfcd7b860

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/nersc_qa.v2/2e0cfcd7b860/0/run.json`

### User Prompt

````text
What SLURM command provides detailed information about why a pending job has not started?
````

### Model Answer

````text
## SLURM Command for Pending Job Diagnostics

The command you're looking for is:

```bash
squeue --job <job_id> --start
```

But more specifically, the most useful command is:

```bash
scontrol show job <job_id>
```

This provides detailed job information including the **`Reason`** field explaining why the job is pending.

---

### Most Direct Answer

```bash
squeue -j <job_id> -o "%.18i %.9P %.8j %.8u %.8T %.10M %.9l %.6D %R"
```

The **`%R`** field shows the **reason** for the pending state.

---

### Common Pending Reasons You Might See

| Reason | Meaning |
|--------|---------|
| `Resources` | Waiting for sufficient resources |
| `Priority` | Higher priority jobs ahead in queue |
| `QOSMaxCpuPerUserLimit` | User CPU limit reached |
| `Dependency` | Waiting on another job |
| `ReqNodeNotAvail` | Requested nodes unavailable |
| `PartitionTimeLimit` | Job exceeds partition time limit |

---

### Quick Tip

```bash
squeue --job <job_id> --reason
```

Would you like help interpreting a specific pending reason? 😊
````

### Reference Answer

Answer: The `squeue --reason -j <jobid>` command or `scontrol show job <jobid>` shows the reason a job is pending.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: Use squeue --reason -j <jobid> or scontrol show job <jobid> to see why a pending job has not started.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional useful information.
````

---

## 8. lang_sonnet_base | qa | borderline | 44d3400b69bc

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/nersc_qa.v2/44d3400b69bc/0/run.json`

### User Prompt

````text
How does a user restore an accidentally deleted file from Home using snapshots?
````

### Model Answer

````text
# Restoring an Accidentally Deleted File Using Snapshots

Here's a step-by-step guide to recover your file! 😊

---

## Method 1: Via File Manager (GUI)
1. **Open your File Manager** and navigate to your **Home** directory
2. Look for a **"Previous Versions"** or **"Snapshots"** option (right-click on the folder)
3. Browse available snapshots by date/time
4. **Select the snapshot** from before the file was deleted
5. **Copy or restore** the file to your desired location

---

## Method 2: Via Terminal
If snapshots are stored in a `.snapshots` directory:

```bash
# List available snapshots
ls ~/.snapshots/

# Browse a specific snapshot
ls ~/.snapshots/<snapshot-id>/snapshot/

# Copy the file back
cp ~/.snapshots/<snapshot-id>/snapshot/filename ~/filename
```

---

## Method 3: Using Snapper (Linux)
```bash
# List snapshots
snapper list

# Restore a specific file
snapper -c home undochange <snapshot-number>..0 /home/user/filename
```

---

## ⚠️ Tips
- Act **quickly** — newer snapshots may overwrite older ones
- Check your system's **snapshot schedule** to know how far back you can go
- **Don't save new files** to the same location before restoring

---

Would you like more details about a specific snapshot tool or operating system? I'm happy to help! 🙂
````

### Reference Answer

Answer: Navigate to the `.snapshot` directory inside the directory where the file was, choose the desired snapshot timestamp, and copy the file back to the original location.

Source doc: https://docs.nersc.gov/filesystems/home/

Section: Home FS

Source passage: To restore a file, navigate to the .snapshot directory, choose the snapshot with the desired timestamp, and copy the file back to its original location.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response provides a good overall solution, but it uses a different path for the snapshot directory and provides additional methods. The core steps are similar to the reference solution.
````

---

## 9. lang_sonnet_base | qa | fail_or_skip | ea640da45b77

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/nersc_qa.v2/ea640da45b77/0/run.json`

### User Prompt

````text
What is the NERSC Globus endpoint name for Perlmutter?
````

### Model Answer

````text
The NERSC Globus endpoint name for Perlmutter is:

**`nersc#perlmutter`**

You can use this endpoint to transfer data to and from Perlmutter via Globus. Make sure you have a NERSC account and are authenticated through Globus to access it.

Is there anything else you'd like to know? 😊
````

### Reference Answer

Answer: The NERSC Globus endpoint is `nersc#dtn`.

Source doc: https://docs.nersc.gov/data/transferring/

Section: Transferring Data

Source passage: The NERSC Globus endpoint for data transfers is nersc#dtn.

### Automated Judgment

- Status: `scored`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
The provided endpoint `nersc#perlmutter` does not match the expected `nersc#dtn`. Ensure you're referencing the correct endpoint as per the task requirements.
````

---

## 10. lang_sonnet_base | ticket | clear_pass | INC0241972_spin_cronjob_webhook_annotations

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/ticket_cases/INC0241972_spin_cronjob_webhook_annotations/0/run.json`

### User Prompt

````text
A SPIN CronJob fails to start pods and events show admission-webhook denials about missing `nersc.gov/*` annotations and UID/GID mismatch checks.

What is the likely issue and fix path?
````

### Model Answer

````text
## Diagnosis: SPIN Admission Webhook Rejecting CronJob Pods

This is a **NERSC SPIN-specific issue** where the admission webhook enforces security policies before pods are scheduled.

---

## Likely Root Causes

### 1. Missing Required `nersc.gov/*` Annotations
SPIN's webhook requires specific annotations on workloads:

```yaml
# Common required annotations
metadata:
  annotations:
    nersc.gov/collab_uids: "12345"        # Authorized UID(s)
    nersc.gov/collab_gids: "12345"        # Authorized GID(s)
    nersc.gov/roles: "user"               # Role definition
```

### 2. UID/GID Mismatch
The container's `securityContext` UID/GID must **match your NERSC account's actual UID/GID**:

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsUser: <YOUR_NERSC_UID>       # Must match nersc.gov/collab_uids
        runAsGroup: <YOUR_NERSC_GID>      # Must match nersc.gov/collab_gids
        fsGroup: <YOUR_NERSC_GID>
```

---

## Fix Path

### Step 1 — Look Up Your NERSC UID/GID
```bash
# From a NERSC login node (Perlmutter, etc.)
id $USER
# uid=12345(username) gid=12345(group)
```

### Step 2 — Correct CronJob Manifest
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: my-cronjob
  namespace: my-namespace
  annotations:
    nersc.gov/collab_uids: "12345"
    nersc.gov/collab_gids: "12345"
spec:
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      template:
        metadata:
          annotations:
            nersc.gov/collab_uids: "12345"   # ⚠️ Required on pod template too
            nersc.gov/collab_gids: "12345"
        spec:
          securityContext:
            runAsUser: 12345                  # Must match annotation
            runAsGroup: 12345
            fsGroup: 12345
          containers:
          - name: my-container
            image: registry.nersc.gov/...    # Use NERSC registry
            securityContext:
              allowPrivilegeEscalation: false
```

### Step 3 — Validate Before Applying
```bash
# Dry-run to catch webhook denials early
kubectl apply --dry-run=server -f cronjob.yaml

# Check existing events for denial details
kubectl get events -n my-namespace --sort-by='.lastTimestamp' | grep -i "denied\|webhook"
```

### Step 4 — Verify Running Jobs
```bash
kubectl describe cronjob my-cronjob -n my-namespace
kubectl get pods -n my-namespace --show-labels
```

---

## Key Rules Summary

| Requirement | Detail |
|---|---|
| Annotations location | **Both** `metadata` AND `spec.jobTemplate.spec.template.metadata` |
| UID/GID source | Must come from `id` on a NERSC login node |
| Registry | Use `registry.nersc.gov` (not Docker Hub) |
| Privilege escalation | Must be `false` |

---

## ⚠️ Common Pitfall
> Annotations on the **CronJob metadata only** are insufficient — the webhook validates the **pod template** annotations at pod creation time, which is why the CronJob *exists* but pods *fail to start*.

Check the [NERSC SPIN documentation](https://docs.nersc.gov/services/spin/) or open a ticket at `help.nersc.gov` if UIDs are correct but denials persist.
````

### Reference Answer

Most likely cause: CronJob/pod spec does not satisfy required SPIN policy annotations and security context constraints.

Key clues:
- Admission webhook errors explicitly mention missing `nersc.gov/username|uid|gid|gids` annotations.
- Additional denials cite `runAsUser`/`runAsGroup`/`fsGroup` mismatches.

Correct guidance:
- Update workload spec to include required NERSC identity annotations and matching security context fields.
- Recreate or resubmit CronJob after validation.
- If generated by tooling, fix template defaults to avoid repeated policy rejects.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution, providing a clear and detailed diagnosis and fix path for the issue.
````

---

## 11. lang_sonnet_base | ticket | borderline | INC0247486_premium_qos_access

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/ticket_cases/INC0247486_premium_qos_access/0/run.json`

### User Prompt

````text
I can submit regular jobs, but premium queue jobs are not accessible for my account.

Context:
- `sacctmgr show assoc user=$USER format=Account,QOS -P` does not show `premium`/`gpu_premium` for my project association.
- Our group wants to run urgent jobs in premium.
- We expected premium access to be available already.

What is the likely cause and how do we enable access correctly?
````

### Model Answer

````text
## Likely Cause

Your account/project **lacks the `premium` (and/or `gpu_premium`) QOS association** in Slurm's accounting database. Access to premium queues is not automatic — it must be explicitly granted by HPC support/admins for each project account.

---

## How to Confirm

Run the following and check the `QOS` column:

```bash
sacctmgr show assoc user=$USER format=Account,QOS -P
```

If `premium` or `gpu_premium` is **absent**, the association is missing — this confirms the cause.

---

## How to Enable Access Correctly

### 1. Contact HPC Support
Premium QOS access is typically granted by **submitting a support request**. You (or your PI) should:

- Identify the **project account** that needs access (e.g., `proj_abc`)
- Request addition of `premium`/`gpu_premium` QOS to that account
- Provide **justification** (e.g., urgent deadlines, time-sensitive workflows)

### 2. What Admins Will Run
The admins will execute something like:

```bash
sacctmgr modify account proj_abc set QOS+=premium,gpu_premium
```

### 3. Verify After Grant
Once confirmed by admins, re-check:

```bash
sacctmgr show assoc user=$USER format=Account,QOS -P
```

Then test with:

```bash
sbatch --account=proj_abc --qos=premium your_job.sh
```

---

## ⚠️ Key Notes

| Point | Detail |
|---|---|
| **Who can grant access** | Only HPC admins (not users or PIs directly) |
| **Scope** | Access is per-project-account, not per-user |
| **Turnaround** | Typically 1–2 business days via a support ticket |

---

Would you like help drafting the support request or troubleshooting further?
````

### Reference Answer

Most likely cause: your account association does not currently include premium QOS permissions; premium must be explicitly enabled by project leadership.

Key clues:
- QOS listing for your account omits `premium`/`gpu_premium`.
- Standard queues are visible while premium is not.
- Premium is controlled because it has higher charge factors.

Correct guidance:
- Ask the project PI or PI proxy to enable premium access for the relevant users in Iris.
- Re-check account/QOS association after the PI-side change.
- If access still does not appear after a short delay, contact support to verify association propagation.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response is mostly accurate but differs from the reference solution in terms of who should enable premium access. It provides relevant guidance and commands to confirm and resolve the issue.
````

---

## 12. lang_sonnet_base | ticket | fail_or_skip | INC0240995_jupyter_404_502_spin_degradation

- Judge score: `20`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m2_canonical/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/ticket_cases/INC0240995_jupyter_404_502_spin_degradation/0/run.json`

### User Prompt

````text
Jupyter intermittently returns 404/502 and kernels stop unexpectedly across the morning.

What is the most likely cause?
````

### Model Answer

````text
## Most Likely Cause: Resource Exhaustion or Kernel Memory Crashes

The combination of **intermittent 404/502 errors** + **unexpected kernel deaths** strongly points to:

---

### 🔴 Primary Suspect: Memory (RAM) Exhaustion
When kernels consume too much memory:
- The **OS kills kernels** (OOM Killer) → kernels stop unexpectedly
- The **Jupyter server becomes temporarily unreachable** → 502/404 errors
- It happens **progressively through the morning** as notebooks accumulate data in memory

---

### Other Contributing Causes to Check

| Cause | 404 | 502 | Kernel Death |
|---|---|---|---|
| **OOM / Memory exhaustion** | ✅ | ✅ | ✅ |
| Jupyter server crashing/restarting | ✅ | ✅ | ✅ |
| Proxy/gateway timeout (nginx) | ❌ | ✅ | ❌ |
| Idle kernel culling misconfigured | ❌ | ❌ | ✅ |
| Disk space full | ✅ | ✅ | ✅ |

---

### 🔍 Quick Diagnostic Steps

```bash
# Check OOM events
dmesg | grep -i "killed process"

# Check available memory
free -h

# Check disk space
df -h

# Check Jupyter logs
journalctl -u jupyter --since "today"
```

---

### ✅ Most Likely Fix
- **Increase server RAM** or limit per-kernel memory
- Set `MappingKernelManager.cull_idle_timeout` to reclaim memory from idle kernels
- Restart the Jupyter server and monitor memory usage with `htop`

Would you like help configuring kernel culling or diagnosing a specific environment? 🚀
````

### Reference Answer

Most likely cause: transient Spin/Jupyter backend degradation.

Key clues:
- Mixed 404/502 errors and intermittent recovery.
- Multiple users report similar timing.

Correct guidance:
- Treat as service incident first; retry after stabilization.
- Avoid immediate local environment changes unless issues persist post-recovery.
- Monitor center status for confirmation/resolution updates.

### Automated Judgment

- Status: `scored`
- Score: `20.0`
- Pass: `False`

Rationale:

````text
The agent's response does not match the reference solution's most likely cause and guidance. However, it provides a plausible alternative explanation and relevant diagnostic steps.
````

---

## 13. lang_gptoss_chroma | qa | clear_pass | 924443390b3f

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss__gptoss__6f8b829b/nersc_qa.v2/924443390b3f/0/run.json`

### User Prompt

````text
What is the SLURM command to submit a batch job at NERSC?
````

### Model Answer

````text
At NERSC you submit a batch job with the **`sbatch`** command.  
Typical usage is:

```bash
sbatch my_job_script.sh
```

`sbatch` reads the `#SBATCH` directives in the script (nodes, time, QOS, etc.) and queues the job for later execution — the scheduler then returns a job ID (e.g., “Submitted batch job 864933”) 【source】.
````

### Reference Answer

Answer: The command `sbatch <script.sh>` is used to submit a batch job.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: Use sbatch <script> to submit a batch job to the queue.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional useful context and examples.
````

---

## 14. lang_gptoss_chroma | qa | borderline | aa2a81b8bc73

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss__gptoss__6f8b829b/nersc_qa.v2/aa2a81b8bc73/0/run.json`

### User Prompt

````text
How many A100 GPUs are on each GPU node on Perlmutter?
````

### Model Answer

````text
Each GPU‑accelerated node on Perlmutter is equipped with **four NVIDIA A100 GPUs**【chromadb_query_documents_0】.
````

### Reference Answer

Answer: Each GPU node on Perlmutter has four NVIDIA A100 40 GB GPUs.

Source doc: https://docs.nersc.gov/systems/perlmutter/architecture/

Section: Perlmutter Architecture

Source passage: Each Perlmutter GPU node is equipped with four NVIDIA A100 40 GB Tensor Core GPUs.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response accurately conveys that Perlmutter's GPU nodes have four NVIDIA A100 GPUs. It uses 'GPU-accelerated node' instead of 'GPU node' and omits the '40 GB' detail. Additional formatting and a citation marker are included.
````

---

## 15. lang_gptoss_chroma | qa | fail_or_skip | 0256f6e985b4

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss__gptoss__6f8b829b/nersc_qa.v2/0256f6e985b4/0/run.json`

### User Prompt

````text
What `squeue` flags show only a user's own jobs in a compact format?
````

### Model Answer

````text
Error: Error executing tool chroma_query_documents: Failed to query documents from collection 'slurm_docs': Collection [slurm_docs] does not exist
````

### Reference Answer

Answer: Use `squeue -u $USER --format='%.18i %.9P %.30j %.8u %.8T %.10M %.9l %.6D %R'` or simply `squeue -u $USER` for a default listing.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: squeue -u $USER shows all jobs belonging to the current user. Custom --format strings can control which columns are displayed.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 16. lang_gptoss_chroma | ticket | clear_pass | INC0242097_account_reactivation_vetting_flow

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss__gptoss__6f8b829b/ticket_cases/INC0242097_account_reactivation_vetting_flow/0/run.json`

### User Prompt

````text
A deactivated account needs temporary reactivation for proposal/account tasks, but access cannot be restored immediately.

What steps are typically required?
````

### Model Answer

````text
**Typical steps to get a de‑activated NERSC account re‑activated (even if only temporarily)**  

| Step | What you (or your PI) must do | Why it is needed | Where the guidance comes from |
|------|------------------------------|------------------|------------------------------|
| 1️⃣ Open a request for re‑activation | Send a short e‑mail to **accounts@nersc.gov** (or open a ticket in the NERSC Help Portal) asking that the account be re‑enabled for a specific purpose (e.g., to finish a proposal or to add a project). | The support team must be notified that the account should be moved out of the “expired” state. | *Account Policies – “User‑initiated deactivation”* and *“Account Deactivation Process”*【2†L31-L45】 |
| 2️⃣ Have the PI (or an authorized project manager) approve the request | The PI must add the user back to an **active project** (or create a new one) in Iris. This is the same step that is required when a de‑activated account is “reactivated” after a user‑initiated or PI‑initiated removal. | A NERSC account is only active while it is associated with at least one active allocation. Adding the user to a project re‑establishes that link. | *Account Lifecycle – “Account Creation”* and *“Account Continuation”*【2†L31-L38】 |
| 3️⃣ Account vetting (if required) | If the user’s identity or affiliation has changed, Iris will trigger a short vetting process (typically < 1 week). During vetting the account stays disabled. | NERSC must verify that the person requesting access is the legitimate owner of the username. | *Account Creation* – “NERSC vets the prospective user”【2†L31-L34】 |
| 4️⃣ Password/MFA reset (optional but recommended) | Once the account is re‑enabled, the user should reset the password (via the “Forgot password?” link in Iris) and, if MFA is enabled, re‑configure the MFA token. | De‑activated accounts have their password/MFA cleared; resetting guarantees you can log in. | *Passwords – “Forgotten Passwords”* and *“How To Change Your Password in Iris”*【2†L1-L22】 |
| 5️⃣ Temporary limited access (if the re‑activation is not immediate) | If the account cannot be fully re‑enabled right away, NERSC will place it in a **“data‑access only”** state for up to 60 days (you can still log in to DTNs/HPSS to retrieve data). | This state lets you collect the files you need for the proposal while the full account is being restored. | *Account Deactivation Process – “allocation‑year discontinuation”* (14‑day compute access → 60‑day data‑access only)【2†L45-L53】 |
| 6️⃣ Confirm the default project | After the account is active, verify in Iris that the correct project is set as the **default allocation** (so any jobs you run while the account is active are charged correctly). | If you need to charge to a specific project for the proposal, the default must be set appropriately. | *Account Policies – “Account Deactivation”* (project association)【2†L31-L38】 |
| 7️⃣ Notify the PI when the temporary work is finished | Ask the PI to remove you from the project (or let the project expire) once the proposal/account task is done, so the account can return to its normal de‑activated state. | Prevents the account from staying active longer than needed. | *Account Deactivation – “User‑initiated deactivation”* and *“PI‑initiated project disassociation”*【2†L31-L38】 |

### Summary of the workflow

1. **Submit a re‑activation request** (email or ticket).  
2. **PI adds the user to an active project** in Iris.  
3. **NERSC performs any required vetting** (usually < 1 week).  
4. **Reset password/MFA** once the account is marked “active”.  
5. If the full account cannot be restored immediately, you will be placed in a **data‑access‑only** state for up to 60 days, allowing you to retrieve the files needed for the proposal.  
6. **Set the correct default project** in Iris so any compute you do during the temporary window is charged correctly.  
7. **Close the temporary access** after the task is complete (PI removes you from the project).

These steps follow the standard NERSC account‑lifecycle rules for de‑activated accounts and ensure that the user regains just enough access to finish proposal/account work while keeping the overall security and policy compliance of the facility.
````

### Reference Answer

Most likely process: ORCID/profile validation + vetting completion + temporary project assignment before account reactivation.

Key clues:
- Reactivation request triggers identity/compliance workflow.
- Password setup link is sent only after vetting completes.

Correct guidance:
- Provide required identity fields (ORCID, org details) promptly.
- Wait for vetting completion, then set password and enroll MFA.
- Validate access with updated account status in Iris.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly aligns with the reference solution, providing a detailed and accurate step-by-step guide for reactivating a de-activated NERSC account.
````

---

## 17. lang_gptoss_chroma | ticket | borderline | INC0241382_scratch_quota_applied_wrong_account

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss__gptoss__6f8b829b/ticket_cases/INC0241382_scratch_quota_applied_wrong_account/0/run.json`

### User Prompt

````text
A previously approved scratch quota increase appears missing. Follow-up checks show quota may have been applied to the wrong account (user vs collab account).

How should this be diagnosed and corrected?
````

### Model Answer

````text
**Root‑cause checklist**

| What to look for | Why it matters | Where the evidence lives |
|------------------|----------------|--------------------------|
| **Original request record** (e.g., an Iris or DAS form) – who was listed as the *owner* of the quota (user ID vs. collaboration ID). | The quota‑setting scripts use the *owner* field to decide which Unix account to update. A mismatch will send the change to the wrong account. | Ticket **INC0214247** – the request was entered in Iris but the script skipped the entry because of a timing bug, leaving the quota unchanged for the intended user. |
| **Quota‑propagation logs** (`set_quota` daemon, `quota_update.log`). | These logs show the exact account name that the daemon attempted to update and whether the update succeeded. | Same ticket **INC0214247** shows a “No new quota info to process” message when the timestamp check failed. |
| **Current filesystem quota tables** (`showquota`, `lfs getquota`, `myquota`). | A quick `showquota` on both the *user* account and the *collab* account tells you where the new limits actually landed. | Several other tickets (e.g., **INC0213624**, **INC0202548**) demonstrate the normal verification flow: `showquota` after an `lfs setquota` command. |
| **Audit of DAS quota files** (`/global/cfs/cdirs/nstaff/nquota/...`). | If the quota was applied via the DAS “quota‑file” mechanism, the file name contains the *project* or *account* identifier. A wrong identifier will affect the wrong account. | Ticket **INC0202548** shows a quota file that was correctly picked up by the cron job. |
| **User‑vs‑collab UID/GID mapping** (`id <user>`, `id <collab>`). | The quota‑setting command (`lfs setquota -u <uid> …`) must receive the correct UID. A typo or copy‑and‑paste error can silently give the other account the new limits. | Implicit in all “lfs setquota” tickets (e.g., **INC0213624**, **INC0217605**). |

---

## Step‑by‑step diagnosis

1. **Gather the original request**  
   * Pull the Iris/DAS ticket (or email) that approved the increase.  
   * Confirm the *account* field – is it the individual user’s NERSC username or the collaboration’s group name?  

2. **Check the quota‑propagation logs**  
   ```bash
   grep -i "<requested‑account>" /global/common/software/nersc/pscratch/set_quota.log
   grep -i "No new quota info" /global/common/software/nersc/pscratch/set_quota.log
   ```  
   * Look for entries that reference the *wrong* account name.  
   * In **INC0214247** the daemon logged “No new quota info to process” because the sliding‑window timestamp check dropped the entry – a similar log line will tell you if the request was ignored or mis‑routed.  

3. **Inspect the live quota for both accounts**  
   ```bash
   # User account
   showquota -u <user> /pscratch
   # Collaboration (group) account
   showquota -g <collab> /pscratch
   ```  
   * If the new limits appear under the group account but not under the user, the request was applied to the wrong principal.  

4. **Validate the DAS quota‑file (if the request went through DAS)**  
   ```bash
   cat /global/cfs/cdirs/nstaff/nquota/common_quotas/*<date>.txt | grep <project-or-user>
   ```  
   * Verify that the line contains the correct identifier (`<user>` vs. `<collab>`).  

5. **Cross‑check UID/GID**  
   ```bash
   id <user>
   id <collab>
   ```  
   * Ensure the UID used in any `lfs setquota` command matches the intended user.  

6. **Confirm there are no “sliding‑window” or timing bugs**  
   * The bug described in **INC0214247** (timestamp comparison against a 10‑minute window) can cause a legitimate request to be dropped. If the request timestamp is older than the daemon’s window, the entry will be ignored.  

---

## Corrective actions

| Action | Command / Procedure | When to use |
|--------|----------------------|------------|
| **Re‑apply the quota to the correct account** (manual `lfs setquota`) | ```bash\nlfs setquota -u <correct‑user> -b <new‑block‑quota> -B <hard‑block‑quota> -i <new‑inode‑quota> -I <hard‑inode‑quota> /pscratch\n``` | If the request was approved but never applied, or applied to the wrong UID. |
| **Update the DAS quota file** (if the request is processed by the nightly cron) | Append a line like `myproj --block 100T:105T --files 20M:21M` to `/global/cfs/cdirs/nstaff/nquota/common_quotas/YYYYMMDD.txt` and let the cron run (or trigger it manually with `quota_update.sh`). | When the system uses the quota‑file workflow. |
| **Fix the sliding‑window bug** (if it is still present) | Edit `/global/common/software/nersc/pscratch/set_quota.py` (or the relevant script) to use the *earliest* of `run_time` or `tarball_creation_time` as the reference, as was done in the fix for **INC0214247**. | If the daemon continues to drop entries because of the timestamp check. |
| **Re‑run the daemon** (optional) | ```bash\nsystemctl restart set_quota.service   # or the equivalent NERSC daemon command\n``` | After fixing the script or after adding a corrected entry to the quota file. |
| **Verify the change** | ```bash\nshowquota -u <correct‑user> /pscratch\n``` | Must show the new block and inode limits. |
| **Document the correction** | Add a comment to the original ticket, note the mistaken account, the corrective command, and the verification output. | Provides an audit trail and prevents repeat mistakes. |

---

## Example of a complete remediation (based on the evidence)

1. **Identify the mistake** – the original Iris request (Ticket INC0214247) listed user *jsmith* but the `set_quota` daemon logged “No new quota info to process” because the entry fell outside the 10‑minute window. The quota was never written for *jsmith*; a later manual `lfs setquota` had been run for the collaboration group *climate‑proj* instead.  

2. **Apply the correct quota**  
   ```bash
   # Desired limits: 100 TB block, 105 TB hard, 20 M inode, 21 M hard
   lfs setquota -u jsmith -b 100T -B 105T -i 20M -I 21M /pscratch
   ```

3. **Confirm**  
   ```bash
   $ showquota -u jsmith /pscratch
   | pscratch | 6.57TiB | 100.00TiB | 6.6% | 20.00M | 21.00M |
   ```

4. **Update the ticket** – note that the original request was applied to the wrong account, the bug has been patched (see **INC0214247**), and the quota now appears correctly for the user.

---

### TL;DR – What you need to do

1. **Locate the original request** and verify the intended *user* vs. *collaboration* identifier.  
2. **Search the `set_quota` (or DAS) logs** for that identifier – look for “No new quota info” or a record under the wrong name.  
3. **Run `showquota` for both accounts** to see where the new limits actually landed.  
4. **If the quota is on the wrong account, re‑apply it** with `lfs setquota` (or edit the DAS quota file) using the correct UID.  
5. **If the daemon dropped the entry**, fix the sliding‑window timestamp logic (as was done in ticket INC0214247) and restart the daemon.  
6. **Verify** with `showquota` and close the ticket with a clear audit note.

Following these steps will pinpoint whether the quota increase was mis‑routed, let you correct it safely, and ensure the same mistake does not recur.
````

### Reference Answer

Most likely cause: quota change was applied to a different identity target than intended (for example personal user instead of shared/collab account).

Key clues:
- Approval exists but observed quota values remain unchanged for expected account.
- Verification tools show mismatch between requested target and updated target.

Correct guidance:
- Verify quota values on the exact account/entity that should receive the change.
- Request correction to apply limits/inode values to the intended account.
- Confirm new quota + expiration after update propagates.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response is comprehensive and provides a clear guide on how to diagnose and correct the issue. However, it does not directly match the concise and to-the-point reference solution.
````

---

## 18. lang_gptoss_chroma | ticket | fail_or_skip | INC0240578_shifter_image_gateway

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss__gptoss__6f8b829b/ticket_cases/INC0240578_shifter_image_gateway/0/run.json`

### User Prompt

````text
On Perlmutter, I suddenly cannot start container jobs and I get:

$ shifterimg images
ERROR: failed to contact the image gateway.

$ shifter --image=nersc/pytorch:24.08.01 --module gpu,nccl-plugin ...
FAILED to lookup docker image nersc/pytorch:24.08.01

Context:
- This started abruptly.
- The same image and workflow had worked previously.
- Behavior improved briefly, then reappeared, and later stabilized again.

What should I check first, and what is the likely root cause?
````

### Model Answer

````text
Error: Error executing tool chroma_query_documents: Failed to query documents from collection 'perlmutter_docs': Collection [perlmutter_docs] does not exist
````

### Reference Answer

Most likely cause: a transient service-side issue with the Shifter image gateway/backend, not a user image-name typo.

Key clues:
- `shifterimg images` cannot contact the image gateway.
- The same image reference worked before.
- Symptoms were intermittent (disappeared and reappeared) and then stabilized.

Correct guidance:
- First run a quick service-health check command like `shifterimg images`.
- Retry after a short delay when symptoms look transient.
- If it persists, escalate with timestamp, exact image reference, and full error output so operations can investigate gateway-side problems.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 19. lang_sonnet_chroma | qa | clear_pass | 1a0fb8e92302

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet__claude_sonnet__228d8f84/nersc_qa.v2/1a0fb8e92302/0/run.json`

### User Prompt

````text
How can a NERSC user submit a help ticket?
````

### Model Answer

````text
Based on the retrieved documentation, here is a comprehensive guide on how a NERSC user can submit a help ticket:

---

## How to Submit a Help Ticket at NERSC

### 🖥️ Primary Method: Online Help Desk (Preferred)
The **preferred** method for contacting NERSC is through the **online help desk**:
- 🔗 **https://help.nersc.gov/**

Access requires logging in with your **NERSC username, password, and one-time password (OTP/MFA)**. Tickets submitted via the portal are automatically placed in the **"Consulting COD"** queue in ServiceNow.

> *Source: `docs` collection – `getting-started.md`, "Getting Help" section*

---

### 📧 Email (If You Can't Log In)
If you are an **existing user unable to log in** to the help portal, you can email:
- **accounts@nersc.gov** – for account support
- **allocations@nersc.gov** – for allocation-related queries

If you are **not a NERSC user**, these same email addresses apply.

> *Source: `docs` collection – `getting-started.md`, "Getting Help" section*

---

### 📞 Phone (Critical System Issues Only)
Phone support for consulting and account inquiries has been **suspended**, but for **urgent/critical system issues** you may call:
- 🇺🇸 **1-800-66-NERSC** (USA only)
- 🌍 **1-510-486-8600**, Option 1

> *Source: `docs` collection – `getting-started.md`, "Operations/Phone Support" section*

---

### 📅 Schedule a 1-on-1 Appointment
NERSC also offers **30-minute expert appointments** for topics such as NERSC 101, GPU programming, containers, filesystems, and more:
- 🔗 **https://nersc.as.me**

---

### ✅ Tips for Filing a Good Ticket
To help NERSC consultants resolve your issue quickly, include as much of the following as possible:
- **Error messages**
- **Job IDs**
- **Location of relevant files** (input/output, job scripts, source code, executables)
- Output of `module list`
- **Steps you have already tried**
- **Steps to reproduce** the issue

Paste text directly into the ticket rather than using screenshots (unless the graphical output itself is the issue). You can also improve readability of code/output snippets by wrapping them with `[code]<pre>` and `</pre>[/code]` tags.

> *Source: `docs` collection – `getting-started.md`, "How to File a Good Ticket" section*

---

### ⏰ Support Availability
Account support is available **8 AM – 5 PM Pacific Time, Monday–Friday (business days)**. NERSC aims to respond to new tickets within **4 business hours** and resolve or communicate a path to resolution within **3 business days (27 business hours)**.

> *Source: `consulting_docs` collection – `roles-and-expectations/index.md`, "Ticket States & SLAs" section*
````

### Reference Answer

Answer: Users can submit tickets through the NERSC help portal at `help.nersc.gov` or by emailing `accounts@nersc.gov` for account issues.

Source doc: https://docs.nersc.gov/

Section: Support

Source passage: Submit support tickets at help.nersc.gov or contact the NERSC help desk by email.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional relevant information.
````

---

## 20. lang_sonnet_chroma | qa | borderline | 7b4feff6a3c2

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet__claude_sonnet__228d8f84/nersc_qa.v2/7b4feff6a3c2/0/run.json`

### User Prompt

````text
What is Shifter and why would a NERSC user use it?
````

### Model Answer

````text
Here is a comprehensive answer based on the retrieved NERSC documentation:

---

## What is Shifter?

**Shifter** is a software package developed by NERSC that allows users to run container images — such as Docker images — securely on HPC systems at scale. It was purpose-built to bring the flexibility of Linux containers to the HPC environment.

> *"Shifter is a software package that allows user-created images to run at NERSC. These images can be Docker images or other formats."*
> — [`development/containers/shifter/how-to-use.md`]

### How It Works

Shifter works by:
1. **Pulling images** from a registry like Docker Hub via the `shifterimg pull` command.
2. **Converting** Docker images into a flattened format that can be efficiently distributed and launched on HPC compute nodes.
3. **Mounting** the flattened image via a loop mount on compute nodes, which moves metadata operations (like file lookup) to the compute node rather than relying on central parallel file system metadata servers.

---

## Why Would a NERSC User Use Shifter?

There are several compelling reasons:

### 1. 🧪 Custom Software Environments
Users can package their entire software stack — including the base OS, libraries, and dependencies — into a container image and run it exactly as-is on NERSC systems. This eliminates the need to recompile or reconfigure software for NERSC's specific environment.

### 2. 🔁 Reproducibility & Portability
Since Docker images can run on any Docker-friendly system, a Shifter image built for NERSC can also be used at other computing centers. This promotes reproducible science and portable workflows.

### 3. ⚡ Performance — Especially for Python
Shifter offers **significant performance improvements** for applications that rely heavily on shared libraries, such as Python. By mounting images via loop mount on compute nodes, it avoids expensive metadata operations on the parallel file system (Lustre). Benchmarks using the *pynamic* benchmark show Shifter essentially matches the performance of a single Docker instance on a workstation.

> *"It is currently the best performing option for python code stacks across multiple nodes."*
> — [`development/containers/shifter/how-to-use.md`]

### 4. 📦 I/O Performance via Volume Mounting
Shifter's volume mounting capabilities can provide **local-disk-like I/O performance**, which is valuable for I/O-intensive workloads.

### 5. 🖥️ Flexible Usage
Shifter can be used:
- **Interactively** on login nodes
- In **batch jobs** via Slurm (using `#SBATCH --image=...` and `srun shifter ...`)
- In **interactive Slurm jobs** (`salloc`)

### 6. 🔒 Security
Private images pulled by a user are only accessible to that user, not the broader community.

---

## ⚠️ Important Note

NERSC is **gradually phasing out Shifter** in favor of **`podman-hpc`**. New users are encouraged to start with `podman-hpc` instead:

> *"While we still support Shifter, NERSC eventually plans to phase it out in favor of podman-hpc. If you are a beginner, you should consider starting with podman-hpc rather than Shifter."*
> — [`development/containers/shifter/shifter-beginner-tutorial.md`]

That said, Shifter remains a fully supported fallback — for example, it was recommended as the container runtime during a period in September 2024 when Podman and Apptainer were temporarily disabled.

---

**Sources:** `development/containers/shifter/index.md`, `development/containers/shifter/how-to-use.md`, `development/containers/shifter/shifter-beginner-tutorial.md`
````

### Reference Answer

Answer: Shifter is a container runtime for HPC that allows users to run Docker-like images on NERSC systems. Users would use it to bring portable, reproducible software environments without requiring root access.

Source doc: https://docs.nersc.gov/software/shifter/

Section: Shifter Containers

Source passage: Shifter allows users to run container images (similar to Docker) on NERSC HPC systems without requiring root privileges, providing portable and reproducible software environments.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response is comprehensive and accurately describes Shifter and its uses. It provides more detail than the reference solution.
````

---

## 21. lang_sonnet_chroma | qa | fail_or_skip | bb7c6d297dae

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet__claude_sonnet__228d8f84/nersc_qa.v2/bb7c6d297dae/0/run.json`

### User Prompt

````text
Where are storage charges applied for files in Community vs Home filesystems?
````

### Model Answer

````text
Error: Error executing tool chroma_query_documents: Failed to query documents from collection 'hpc_docs': Collection [hpc_docs] does not exist
````

### Reference Answer

Answer: Files in Community and Common are charged to the project. Files on Home and Scratch are charged to the file owner, even if stored in another user's directory.

Source doc: https://docs.nersc.gov/filesystems/

Section: Usage Limits

Source passage: Files in the Community (CFS) and Common file systems are charged to the project, while files on the Home and Scratch file systems are charged to the file owner; your files in another user's directory will still be charged to your quota.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 22. lang_sonnet_chroma | ticket | clear_pass | INC0240847_colab_backend_not_supported

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet__claude_sonnet__228d8f84/ticket_cases/INC0240847_colab_backend_not_supported/0/run.json`

### User Prompt

````text
Can I run a Jupyter server on Perlmutter and attach it directly to Google Colab via port forwarding and custom allow-origin settings?

Context:
- Workflow works on another system with SSH tunneling.
- I want to replicate this backend attachment model at NERSC.

Is this supported?
````

### Model Answer

````text
I now have comprehensive evidence from the knowledge base. Here is a detailed, evidence-backed answer:

---

## Running a Jupyter Server on Perlmutter for Google Colab Attachment: **Not Supported**

The short answer is: **this workflow is not supported at NERSC**, and there are specific security policies that block the key mechanisms it relies on. Here's the full breakdown:

---

### ❌ Why This Won't Work at NERSC

#### 1. JupyterHub API Token Generation Is Disabled

The Google Colab "Connect to a local runtime" backend-attachment model requires generating a JupyterHub/Jupyter API token so that Colab can authenticate to your Jupyter server. **NERSC explicitly disables this.**

> *"JupyterHub tokens have a broader scope than is permitted by our security policies and are therefore disabled for this use case."*
> — **INC0218507** (Jupyter POC, April 2024)

The same ticket documents the 403 error you would hit:
> *"Failed to fetch user info, Forbidden (403) with message `{'status': 403, 'message': 'Action is not authorized with current scopes; requires any of [servers]'}`"*

Even if you could get a token, existing tokens **do not include the required `servers` scope**, and NERSC has stated that **no changes to token scoping are planned**.

#### 2. Custom `allow-origin` / CORS Settings Are Not User-Configurable

The Colab local-runtime model requires the Jupyter server to be configured with permissive `allow_origin` (CORS) headers so that `colab.research.google.com` can make cross-origin requests to your kernel. At NERSC, **users do not have permission to modify global Jupyter server configuration**, as confirmed in a related incident:

> *"Support explained that the hosted JupyterLab already includes the extension but it is disabled by default, and instructed the user to create a personal `~/.jupyter/labconfig/page_config.json` file... [the user] lacked permission to modify the global Jupyter server configuration."*
> — **INC0216083** (Jupyter POC, February 2024)

NERSC's JupyterHub is a managed, multi-user service — users cannot pass arbitrary `--NotebookApp.allow_origin='*'` flags to the spawned server.

#### 3. SSH Port Forwarding Alone Is Insufficient

While SSH tunneling to Perlmutter login nodes **is** possible (external SSH access has been enabled since October 2021 per the Perlmutter timeline), port forwarding alone cannot overcome the token/CORS restrictions above. The tunnel would expose a port on your local machine, but Colab needs a valid token *and* permissive origin headers to attach — neither of which NERSC permits.

---

### ✅ What IS Supported: The SSH Tunnel + Local IDE Model

The approach NERSC *does* endorse (for a similar external-IDE-to-compute-node attachment use case) is:

> *"The user was advised to use an SSH tunnel to start Jupyter on the compute node and connect via VSCode as an alternative."*
> — **INC0218507**

This works because **VSCode's Jupyter extension** communicates differently — it does not rely on the JupyterHub token/server scope mechanism in the same way Colab does.

---

### 📋 Summary Table

| Requirement | Status at NERSC |
|---|---|
| SSH tunnel to Perlmutter | ✅ Supported |
| JupyterHub API token generation | ❌ Disabled by security policy |
| Custom `allow-origin` / CORS settings | ❌ Not user-configurable |
| Google Colab "local runtime" backend attach | ❌ **Not supported** |
| VSCode + SSH tunnel to compute node Jupyter | ✅ Supported workaround |

---

### 🔧 Recommended Alternatives

1. **Use [jupyter.nersc.gov](https://jupyter.nersc.gov) directly** — NERSC's managed JupyterHub gives you full access to Perlmutter compute nodes without any tunneling. You can run notebooks in batch jobs billed to your allocation.
2. **Use VSCode with the Remote-SSH + Jupyter extension** — SSH tunnel to a compute node, start a Jupyter server manually, and attach VSCode locally. This is the NERSC-endorsed workaround for external IDE attachment.
3. **Migrate your Colab notebooks to NERSC JupyterLab** — Most Colab workflows transfer directly; NERSC supports custom Conda kernels, containers (Shifter/podman-hpc), and GPU nodes.

If you believe your use case has a compelling scientific justification, you can open a ticket at [help.nersc.gov](https://help.nersc.gov) to discuss with the Jupyter POC team — but based on current policy, an exception is unlikely.
````

### Reference Answer

Most likely answer: this backend integration path is not supported at NERSC due to network/security constraints.

Key clues:
- Request depends on exposing/tunneling Jupyter service to external Colab integration pattern.
- NERSC support explicitly cites security/network policy limitations.

Correct guidance:
- Use supported NERSC Jupyter workflows instead of direct Colab-backend attachment.
- If external integration is required, consult security/network policy first and expect restrictions.
- Do not rely on local ad hoc token/allow-origin tunneling patterns for production workflows.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional details and evidence to support the answer.
````

---

## 23. lang_sonnet_chroma | ticket | borderline | INC0241945_jupyter_servers_hanging

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet__claude_sonnet__228d8f84/ticket_cases/INC0241945_jupyter_servers_hanging/0/run.json`

### User Prompt

````text
Jupyter servers (login/exclusive CPU) hang on start/stop with the message:

`Your server is stopping. You will be able to start it again once it has finished stopping.`

Context:
- Multiple server types are affected during the same window.

What is the likely cause?
````

### Model Answer

````text
The evidence is comprehensive and consistent. Here is the full diagnosis:

---

## Diagnosis: JupyterHub Backend Service Degradation / Outage

### Summary

When **multiple server types** (login nodes *and* exclusive CPU nodes) hang simultaneously on start/stop with the identical message:

> *"Your server is stopping. You will be able to start it again once it has finished stopping."*

the root cause is almost certainly a **JupyterHub backend service problem**, not a per-user issue. This is the critical differentiator: individual user issues (stale state, quota, bad config) affect only that user's session; a JupyterHub service degradation affects all server types across all users in the same window.

---

### Evidence from the Knowledge Base

| Ticket | Key Evidence |
|---|---|
| **INC0235568** | Exclusive CPU node blocked waiting for resources *and* login node stuck stopping simultaneously — resolved by terminating the underlying job and **restarting the service**. |
| **INC0235567** | Login node and exclusive CPU node both stuck in stopping state for hours — *"server is still running and consuming resources"* — resolved after support intervention. |
| **INC0235595** | Login node and exclusive CPU node both unresponsive — stop button non-functional — resolved after support-side corrective action. |
| **INC0237005** | Login node stuck in stopping state — explicitly attributed to *"issues with the Jupyter service overnight"* — resolved after the **service was restored**. |
| **INC0235573** | Login node hung for hours, orphaned jobs being created even after cancellation — resolved by support applying corrective actions to JupyterHub. |
| **INC0235537** | Single-user stuck in stopping state — resolved by support performing a **forced reset of the JupyterHub environment**. |
| **INC0214299** | JupyterHub 403 errors across users — confirmed **JupyterHub performance degradation** — resolved by engineers fixing the backend. |

> *"There were some issues with the Jupyter service overnight."* — INC0237005
> *"Support cleared the stuck Jupyter server (by terminating the underlying job and restarting the service)."* — INC0235568

---

### Why Multiple Server Types Being Affected Is the Key Signal

The Jupyter reference docs confirm that login node servers and exclusive CPU node servers use **completely different backend mechanisms** (login node processes vs. Slurm batch jobs in the `jupyter` QOS). For both to fail in the same time window, the failure must be in the **shared JupyterHub control plane** — the hub process, its database/state store, or the proxy — not in any one server type's provisioning path.

---

### Recommended Actions

1. **Escalate immediately to the Jupyter POC / ops team** — this is a service-level incident, not a user-level issue.
2. **Check JupyterHub service health** — look for hub process errors, database connection failures, or proxy issues in the JupyterHub logs.
3. **Identify and terminate orphaned jobs** — stuck servers often leave behind Slurm jobs consuming resources (check `squeue` for `jupyter` QOS jobs).
4. **Perform a JupyterHub service restart** — past incidents were resolved by restarting the hub service and/or forcing a reset of stale server state in the hub database.
5. **Post a system notice** — if the window spans multiple users, post to the status page so users don't keep retrying and compounding orphaned job accumulation.
6. **Per-user workaround (if needed before service fix):** Support can perform a **forced reset of the individual user's JupyterHub environment** to clear stale stopping state (as in INC0235537), but this will not address the underlying service problem.
````

### Reference Answer

Most likely cause: transient Jupyter backend/platform instability rather than user notebook configuration.

Key clues:
- Multiple server types show same stuck state.
- Issue self-resolves after incident window.

Correct guidance:
- Check status page for active service degradation.
- Retry after backend recovery before changing local environments.
- Escalate only if stuck state persists after status normalization.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response is comprehensive and accurate but could be improved by following the guidance provided in the reference solution more closely, particularly with regards to when to escalate the issue.
````

---

## 24. lang_sonnet_chroma | ticket | fail_or_skip | INC0241968_spin_filesystem_postgres_mismatch

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet__claude_sonnet__228d8f84/ticket_cases/INC0241968_spin_filesystem_postgres_mismatch/0/run.json`

### User Prompt

````text
Spin workloads fail to restart after filesystem-related errors; PostgreSQL container startup also fails.

Context:
- Errors mention container runtime startup and mount-related problems.
- Root cause eventually involved PostgreSQL version mismatch.

How should this be triaged?
````

### Model Answer

````text
Error: Error executing tool chroma_query_documents: Failed to query documents from collection 'hpc_ops': Collection [hpc_ops] does not exist
````

### Reference Answer

Most likely diagnosis: overlapping platform/storage instability plus workload-specific DB version/config mismatch in PostgreSQL deployment.

Key clues:
- Broad filesystem restart problems impact many pods.
- Remaining blocker narrows to PostgreSQL workload/version compatibility.

Correct guidance:
- First isolate platform-wide symptoms from app-specific config errors.
- Verify PostgreSQL image/data compatibility during restart/recovery.
- Track dependent workload recovery after DB fix to confirm full service restoration.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 25. lang_gptoss_chroma_opt | qa | clear_pass | e119dee69e0f

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss_opt__gptoss__92b1c395/nersc_qa.v2/e119dee69e0f/0/run.json`

### User Prompt

````text
What is the difference between `sbatch` and `salloc` for running interactive jobs?
````

### Model Answer

````text
**Short answer**

| Command | What it does | Typical use for an *interactive* workflow |
|---------|--------------|------------------------------------------|
| **`sbatch`** | Submits a **batch script** to the scheduler. The script runs on the allocated nodes without a live user shell. | You can still get an interactive feel by putting a `srun --pty bash` (or similar) inside the script, but the job is still launched as a *batch* job – you don’t get a prompt until the script starts executing. |
| **`salloc`** | **Allocates resources** and then drops you into an interactive shell (or any command you specify). It is essentially a wrapper around `srun` that only reserves the resources. | Directly gives you a prompt on the allocated node(s). From that prompt you run `srun` (or `srun --pty …`) to launch parallel tasks. No separate script is needed. |

**Why the difference matters**

* **Scheduling semantics** – `sbatch` creates a *job* that the scheduler treats like any other batch job (it can be queued, back‑filled, have a time‑limit, etc.). `salloc` creates an *allocation*; the scheduler still queues it, but once the allocation is granted you are immediately handed control, which is why it is the preferred way to start an interactive session.

* **Control flow** – With `sbatch` the control flow is defined entirely by the script you submit. With `salloc` you get a live shell first, then you decide what `srun` commands to issue. This makes it easier to experiment, debug, or run a series of ad‑hoc commands.

* **Resource specification** – Both commands accept the same SLURM options (`--nodes`, `--time`, `--partition`, `--gpus`, etc.). The only practical difference is that `salloc` must be given a command (or defaults to launching a shell) that runs **after** the allocation is granted.

**Evidence from the documentation**

* The *Interactive Jobs* page describes `salloc` as “used to allocate resources in real time to run an interactive batch job… allocate resources and spawn a shell. The shell is then used to execute `srun` commands”【docs, interactive.md, chunk 0】.  
* The *Best Practices* page notes that core‑specialization flags (`-S/--core-spec`) can be used in a **batch script with `sbatch`** but cannot be requested with `salloc`, because `salloc` is already a wrapper for `srun`【docs, best‑practices.md, chunk 9】. This underscores that `sbatch` is the vehicle for full batch‑script features, while `salloc` is limited to allocation‑time options.

**Practical guidance**

* **When you want a reproducible, script‑driven job** (e.g., a large MPI run, a workflow that can be fully described in a file), use `sbatch`.  
* **When you need a quick, interactive session** (testing code, debugging, running a few `srun` commands manually), use `salloc`.  

If you already have a batch script but need to test it interactively, you can either:

1. Run `salloc …` to get a shell, then execute the script manually with `srun` inside, **or**  
2. Add `srun --pty bash` (or `srun --pty <your‑command>`) near the top of the script and submit it with `sbatch`. The job will start, allocate nodes, and then give you an interactive prompt once the script reaches that line.

In short: **`sbatch` = “run a script”**, **`salloc` = “give me a shell on allocated nodes”**. Use the one that matches whether you need a scripted batch job or an on‑the‑fly interactive session.
````

### Reference Answer

Answer: `sbatch` submits a script to run non-interactively in the queue. `salloc` requests an interactive allocation where the user can type commands directly on the allocated nodes.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: sbatch submits a non-interactive batch script. salloc creates an interactive allocation, granting the user a shell prompt on the compute nodes.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional relevant details.
````

---

## 26. lang_gptoss_chroma_opt | qa | borderline | 0256f6e985b4

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss_opt__gptoss__92b1c395/nersc_qa.v2/0256f6e985b4/0/run.json`

### User Prompt

````text
What `squeue` flags show only a user's own jobs in a compact format?
````

### Model Answer

````text
**Flags you need**

| Flag | What it does |
|------|--------------|
| `--me` (or `-u $USER`) | Limits the output to **only the jobs owned by the invoking user**. |
| `-h` | Suppresses the header line, giving a **compact, one‑line‑per‑job** view. |
| `-o <format>` *(optional)* | Lets you define a **custom, terse column layout** (e.g. `-o "%.7i %.2t %.9P %.8j %.8u %.10M %.6D %R"`). |

**Typical compact command**

```bash
squeue --me -h               # user‑only, no header
# or equivalently
squeue -u $USER -h
```

If you want an even tighter column set, add `-o`:

```bash
squeue --me -h -o "%.7i %.2t %.9P %.8j %.8u %.10M %.6D %R"
```

*Evidence*: the documentation shows that `squeue --me` (or `squeue -u $USER`) displays only the current user’s jobs 【2†L31-L38】, and the standard `squeue` flag `-h` removes the header line for a compact listing. Combining these flags gives exactly the view you asked for.
````

### Reference Answer

Answer: Use `squeue -u $USER --format='%.18i %.9P %.30j %.8u %.8T %.10M %.9l %.6D %R'` or simply `squeue -u $USER` for a default listing.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: squeue -u $USER shows all jobs belonging to the current user. Custom --format strings can control which columns are displayed.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response provides a good understanding of the task and offers relevant commands, although with a different format specification. It achieves a similar goal as the reference solution but doesn't directly match it.
````

---

## 27. lang_gptoss_chroma_opt | qa | fail_or_skip | 0dc9361e237f

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss_opt__gptoss__92b1c395/nersc_qa.v2/0dc9361e237f/0/run.json`

### User Prompt

````text
What is the recommended SSH config snippet to enable multiplexing to NERSC?
````

### Model Answer

````text
Error: Recursion limit of 24 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key.
For troubleshooting, visit: https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT
````

### Reference Answer

Answer: Add a `Host perlmutter.nersc.gov` block with `ControlMaster auto`, `ControlPath ~/.ssh/control_%h_%p_%r`, and `ControlPersist 600` to `~/.ssh/config`.

Source doc: https://docs.nersc.gov/connect/

Section: Connecting to NERSC

Source passage: In ~/.ssh/config, add: Host perlmutter.nersc.gov; ControlMaster auto; ControlPath ~/.ssh/control_%h_%p_%r; ControlPersist 600

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 28. lang_gptoss_chroma_opt | ticket | clear_pass | INC0241834_cpu_job_cuda_init_warning

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss_opt__gptoss__92b1c395/ticket_cases/INC0241834_cpu_job_cuda_init_warning/0/run.json`

### User Prompt

````text
A Slurm job intended for CPU-only execution still reports CUDA/GPU-related warnings and behaves unexpectedly.

Context:
- Script requests CPU resources.
- Adding `module load cpu` reduced some issues but warnings remained.
- Application likely has optional GPU initialization paths.

What is the likely cause and fix path?
````

### Model Answer

````text
**Likely cause**

The job itself is *correctly* requesting only CPU resources (`#SBATCH -C cpu …` and no `--gpus‑per‑task`), but the **application you run still tries to initialise the CUDA runtime**.  
Most scientific codes ship with an optional GPU path that is enabled automatically when the CUDA libraries are present in the environment. When no GPU is allocated Slurm leaves `CUDA_VISIBLE_DEVICES` unset (or set to an empty string). The CUDA runtime therefore attempts to open a device, fails, and prints the familiar “CUDA warning: no CUDA‑capable device found” (or similar) before falling back to the CPU implementation. Because the library is still loaded, the warning appears even though the job is running on a CPU‑only node.

Evidence from the documentation:

* The *Running Applications* section explains that **all GPUs allocated to a job are visible to all tasks unless the user explicitly hides them with `CUDA_VISIBLE_DEVICES` or with Slurm’s `--gpu‑bind` flag**【performance/readiness.md_9】.  
* The *Example scripts* page shows a pure‑CPU job script that **must not load any GPU module** and must request the `cpu` constraint【systems/perlmutter/running-jobs/index.md_2】.  
* The *CUDA Debugging* guide notes that the runtime will still try to track GPU allocations even when the user only wants CPU debugging【tools/debug/ddt/index.md_9】.

So the warning you see is not a Slurm allocation problem – it is the application’s own optional GPU initialisation path being triggered because the CUDA libraries are still in the environment.

---

**Fix path**

1. **Make sure no GPU modules are loaded**  
   ```bash
   module purge               # start from a clean environment
   module load cpu           # only the CPU stack you need
   # do NOT load cudatoolkit, cuda, nvhpc, etc.
   ```

2. **Explicitly hide any CUDA runtime that might be on the node**  
   ```bash
   export CUDA_VISIBLE_DEVICES=   # empty string → CUDA sees “no device”
   ```

   (You can also set it to `""` in the job script before the executable is invoked.)

3. **If the application has a run‑time switch to disable GPU support, use it**  
   * Many codes provide `--no-gpu`, `-g 0`, `GPU=0`, or an environment variable such as `USE_CUDA=0`.  
   * Check the application’s documentation or `--help` output.

4. **Re‑compile without GPU support (if you control the build)**  
   * Remove `-DUSE_CUDA` / `-lcudart` etc. from the build flags, or select a “cpu‑only” module if the software is provided as a module (e.g. `module load myapp/cpu`).

5. **Verify the job script really requests a CPU‑only partition**  
   ```bash
   #SBATCH -C cpu               # constraint
   # (do NOT have “#SBATCH -C gpu” anywhere)
   #SBATCH --qos=debug         # or any CPU‑only QoS
   ```

6. **Test the environment inside the allocation**  
   After `srun` starts, run:
   ```bash
   echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
   nvidia-smi   # should say “command not found” on a CPU node
   ldd ./myapp  | grep -i cuda   # should show no CUDA libs linked
   ```
   If any CUDA library is still linked, either unload the module or rebuild the binary.

---

**Summary**

The warnings are caused by the application’s optional CUDA initialisation, not by Slurm. Hide the CUDA runtime (unload GPU modules, set `CUDA_VISIBLE_DEVICES=`) or build/run the program in a true CPU‑only mode. Once the executable no longer sees any CUDA libraries, the warnings disappear and the job behaves as expected.
````

### Reference Answer

Most likely cause: application/runtime stack still attempts CUDA initialization even in CPU allocations.

Key clues:
- CPU queue/request is used but warnings reference CUDA/GPU libraries.
- Behavior persists despite CPU module selection, indicating app-level GPU probing.

Correct guidance:
- Ensure CPU module/stack is loaded and no GPU modules/env vars leak into the run environment.
- Configure application to explicitly disable GPU backend (per app docs/settings).
- If app cannot cleanly disable GPU probing, run on GPU nodes or consult upstream developers.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly identifies the cause of the issue and provides a comprehensive and accurate fix path that aligns with the correct guidance.
````

---

## 29. lang_gptoss_chroma_opt | ticket | borderline | INC0242692_multinode_ofi_fix

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss_opt__gptoss__92b1c395/ticket_cases/INC0242692_multinode_ofi_fix/0/run.json`

### User Prompt

````text
An MPI job runs on 1 CPU node but fails on 2+ nodes with:

`open_fabric(...): OFI fi_getinfo() failed (...: No data available)`

What is the likely fix?
````

### Model Answer

````text
**Likely fix – load a compatible *libfabric* module (or use the temporary‑work‑around version) before launching the job.**  

The error comes from the libfabric provider that MPICH uses during `MPI_Init`. After a system‑maintenance upgrade the default libfabric (e.g., `libfabric/1.22.0`) is no longer compatible with the MPICH version you are using, so the job can start on a single node (where the fabric isn’t exercised) but abort as soon as the MPI fabric is initialized on two or more nodes:

* “OFI fi_getinfo() failed … No data available” – diagnosed as a libfabric incompatibility.  
* The resolution in several tickets was to **load an older libfabric module** (e.g., `module load libfabric/1.20.1`) or the supplied temporary module `libfabric/temp‑workaround`, or to rebuild the application against the newer libfabric.  

```bash
# Example fix
module unload libfabric          # if a newer version is loaded
module load libfabric/1.20.1    # or: module load libfabric/temp-workaround
# then launch the job
srun my_mpi_executable
```

If you prefer to keep the newer libfabric, rebuild/recompile the application after loading the matching MPICH/libfabric stack (or switch to the default programming environment that already has compatible versions).

**In short:** Load a libfabric version that matches the MPICH you are using (or use the temporary libfabric work‑around module) before running the multi‑node MPI job. This restores the `fi_getinfo` call and eliminates the “No data available” error.
````

### Reference Answer

Most likely cause: old MPICH/libfabric compatibility break after Slingshot update.

Key clues:
- Failure appears only in multi-node OFI path.
- Known issue tied to older `cray-mpich` versions.

Correct guidance:
- Rebuild with newer `cray-mpich` (for example 8.1.30).
- Temporary workaround: load `libfabric/temp-workaround` if available.
- Migrate to updated toolchain for durable fix.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response is largely correct and helpful, providing a clear explanation of the issue and a practical workaround. However, for a comprehensive solution, consider including guidance on updating `cray-mpich` and migrating to a newer toolchain for a more durable fix.
````

---

## 30. lang_gptoss_chroma_opt | ticket | fail_or_skip | INC0240608_vasp_binary_missing_mkl

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_chroma_gptoss_opt__gptoss__92b1c395/ticket_cases/INC0240608_vasp_binary_missing_mkl/0/run.json`

### User Prompt

````text
I am rerunning old calculations on Perlmutter with a VASP executable saved in my home directory, and now it fails with:

/global/homes/.../vasp_std: error while loading shared libraries: libmkl_scalapack_lp64.so.2: cannot open shared object file: No such file or directory

Context:
- The same binary worked months ago.
- I only have the executable (no source) for this in-house build.
- This started after a software stack update.

What is the likely cause and what should I do?
````

### Model Answer

````text
Error: Error executing tool chroma_query_documents: Failed to query documents from collection 'vendorbugs.md': Collection [vendorbugs.md] does not exist
````

### Reference Answer

Most likely cause: the old VASP binary depends on Intel/MKL shared libraries that are no longer in the default runtime environment after updates.

Key clues:
- Dynamic loader error for MKL libraries (`libmkl_scalapack_lp64.so.2`, etc.).
- Binary worked previously but fails after environment/software changes.
- User only has a prebuilt executable, so relinking is not immediately possible.

Correct guidance:
- Load the compatibility module stack that restores those Intel mixed libraries (for example `ml intel-mixed`) before launching the binary.
- Confirm dependencies with `ldd vasp_std` to ensure previously missing MKL libs resolve.
- Long-term, rebuild VASP against currently supported libraries/modules to avoid fragile legacy runtime dependencies.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 31. lang_sonnet_chroma_opt | qa | clear_pass | c80b097d98e5

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet_opt__claude_sonnet__c5902b01/nersc_qa.v2/c80b097d98e5/0/run.json`

### User Prompt

````text
Can a NERSC project have multiple top-level Community filesystem directories, and how are quotas managed?
````

### Model Answer

````text
Excellent — the retrieved documentation gives a very complete and authoritative answer. Here's a full breakdown:

---

## NERSC Community Filesystem (CFS): Multiple Directories & Quota Management

### ✅ Yes — A Project Can Have Multiple Top-Level CFS Directories

By default, every NERSC project gets **one** Community directory at:
```
/global/cfs/cdirs/<your_project_name>
```

However, **a PI or PI Proxy can request additional top-level CFS directories** (up to **10 total**) via the [Iris Storage tab](https://iris.nersc.gov). If you need more than 10, you must **open a support ticket**.

---

### 📁 Structural Constraint: Top-Level Only

Due to how quotas are technically implemented, **additional directories can only be created at the top level** of `/global/cfs/cdirs/`. You **cannot** create a separately-quota-managed subdirectory inside an existing directory:

| ✅ Allowed | ❌ Not Allowed |
|---|---|
| `/global/cfs/cdirs/new_directory_name` | `/global/cfs/cdirs/existing_dir/new_directory_name` |

**Workaround:** If you want to present a unified directory structure to your users, you can create **symlinks** inside your main directory pointing to the additional top-level directories:

```bash
nersc$ ls -l /global/cfs/cdirs/existing_directory_name
drwxrws---  3 elvis nstaff   4.0K Feb 18 21:19 random_directory
lrwxrwxrwx  1 elvis nstaff      7 Feb 18 21:20 new_directory_name -> /global/cfs/cdirs/new_directory_name
```

---

### 📊 How Quotas Are Managed

CFS uses **directory-level (fileset) quotas** — unlike Home and Scratch which use user-level quotas. Every file inside `/global/cfs/cdirs/<project>` counts toward *that directory's* quota, regardless of which user wrote it.

**Key quota facts:**

- **Default quota:** 20 TB space / 10M inodes per directory (baseline from ERCAP)
- **Single total allocation:** A project is awarded one total Community storage allocation through the annual **ERCAP** process.
- **Split between directories:** That total allocation **can be distributed** across multiple CFS directories. PIs adjust per-directory quotas via the **Iris Storage tab**:
  1. Go to your project in Iris → **Storage** tab
  2. In the **CFS Directory Usage** table, adjust `Directory Storage Quota (TB)` and/or `Directory File Quota` for each directory
  3. Click **Update Quotas**
  - ⚠️ The **sum of all directory quotas** must not exceed the project's total Storage Allocation and Files Allocation.

- **Mid-year increases:** Require approval from DOE Program Managers — submit a [Disk Quota Increase Form](https://nersc.servicenowservices.com/sp/?id=sc_cat_item&sys_id=f72838ff6ffb420086e96bbeae3ee4d5).

---

### 🔍 Checking Quotas

Use the `showquota` command on Perlmutter login nodes or DTNs:
```bash
showquota <project_name>
```
Or use the [Data Dashboard](https://my.nersc.gov/data-mgt.php) for a per-user/per-group breakdown across all your CFS directories.

---

**Sources:** `docs` collection — `filesystems/community.md`, `filesystems/quotas.md`, `iris/iris-for-pis.md`
````

### Reference Answer

Answer: Yes. A project can request multiple top-level CFS directories, each with its own quota drawn from the project's total allocation. The PI adjusts individual directory quotas in Iris.

Source doc: https://docs.nersc.gov/filesystems/

Section: Community

Source passage: Multiple top-level directories can be created on CFS for a project. Each top-level CFS directory comes with its own quota (drawn out of the total quota allocated for the entire project). The quotas for each top-level directory can be allocated in iris by the project's PI.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional relevant details.
````

---

## 32. lang_sonnet_chroma_opt | qa | borderline | b55d269f600b

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet_opt__claude_sonnet__c5902b01/nersc_qa.v2/b55d269f600b/0/run.json`

### User Prompt

````text
What SLURM directive specifies the allocation account to charge for a job?
````

### Model Answer

````text
The SLURM directive used to specify the **allocation account** to charge for a job is:

## `--account` (short form: `-A`)

### In a batch script (as an `#SBATCH` directive):
```bash
#SBATCH --account=myproject
# or equivalently:
#SBATCH -A myproject
```

### On the command line at submission:
```bash
sbatch -A myproject ./myscript.sl
```

---

### Key details:
- **What it does:** Tells SLURM which project/account to deduct node hours from when the job runs.
- **Default behavior:** If you are a member of only one project, that project is charged automatically. If you belong to **multiple projects**, charges go to your **default project** (as configured in your user portal, e.g., Iris at NERSC) unless you explicitly specify `-A`.
- **When to use it:** Always specify `-A` when you want to charge a non-default project, or as a best practice to make your job scripts unambiguous.

> 📖 *Source: `docs` collection, `jobs/policy.md` — "Assigning Charges" section, and `beginner-guide/index.md` — Slurm flags table.*
````

### Reference Answer

Answer: The `#SBATCH -A <account>` or `#SBATCH --account=<account>` directive specifies the allocation account.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: Use #SBATCH -A <account> or --account=<account> to charge the job to a specific allocation.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response correctly identifies the directive used to specify the allocation account and provides additional useful context and examples. While it deviates from the concise nature of the reference solution, it is considered a good and comprehensive answer.
````

---

## 33. lang_sonnet_chroma_opt | qa | fail_or_skip | 864edf504e6c

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet_opt__claude_sonnet__c5902b01/nersc_qa.v2/864edf504e6c/0/run.json`

### User Prompt

````text
What is the maximum wall clock time for a regular job on Perlmutter?
````

### Model Answer

````text
The answer is clearly documented. Here's a definitive response:

## Maximum Wall Clock Time for the `regular` QOS on Perlmutter

The maximum wall clock time for a **regular** QOS job on Perlmutter is **48 hours**, and this applies to **both GPU and CPU nodes**:

| Node Type | QOS     | Max Time |
|-----------|---------|----------|
| GPU       | regular | **48 hrs** |
| CPU       | regular | **48 hrs** |

> **Source:** `jobs/policy.md` — *QOS Limits and Charges* (Perlmutter GPU and Perlmutter CPU tables)

### Additional context:
- **No node limit** is enforced for the `regular` QOS on either GPU or CPU nodes (though not all nodes may be available at any given time).
- The `regular` QOS has a **submit limit of 5,000 jobs** and **medium priority**.
- Nodes are allocated **exclusively** to each regular QOS job.
- If you need longer runtimes, consider using **checkpointing** or the **`preempt`** QOS (which also allows up to 48 hrs, with a guaranteed 2-hour minimum before preemption).
````

### Reference Answer

Answer: The maximum wall clock time for a regular queue job on Perlmutter is 24 hours.

Source doc: https://docs.nersc.gov/jobs/policy/

Section: Job Policy

Source passage: Jobs in the regular queue on Perlmutter have a maximum wall clock time of 24 hours.

### Automated Judgment

- Status: `scored`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
The agent's response does not match the reference solution. It states the maximum wall clock time is 48 hours, whereas the reference solution states it is 24 hours.
````

---

## 34. lang_sonnet_chroma_opt | ticket | clear_pass | INC0241977_reqnodenotavail_full_reservation

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet_opt__claude_sonnet__c5902b01/ticket_cases/INC0241977_reqnodenotavail_full_reservation/0/run.json`

### User Prompt

````text
A large multi-node job remains pending with:

`ReqNodeNotAvail, UnavailableNodes:nid[...]`

Context:
- Job requests many nodes for long duration.
- Account resources appear sufficient.

What is the likely explanation?
````

### Model Answer

````text
Excellent — I now have strong, well-corroborated evidence from multiple tickets and documentation. Here is the full explanation:

---

## `ReqNodeNotAvail, UnavailableNodes:nid[...]` — Root Cause & Resolution

### 🔍 Most Likely Explanation: A System Reservation Is Blocking the Job

This is the **overwhelmingly common cause** of this error, confirmed by multiple resolved support tickets. Slurm marks nodes as unavailable when they are reserved — either for a **scheduled maintenance window** or an **active compute reservation** (e.g., for another project or a system event). Because the job requests **many nodes for a long duration**, Slurm cannot safely start it without overlapping with the reservation window, so it stays pending indefinitely.

> *"The scheduler indicated the reason `(ReqNodeNotAvail, Reserved for maintenance)`, meaning the requested nodes were reserved for a scheduled maintenance window... Because the job is expected to run longer than the maintenance period, it cannot be scheduled now."*
> — INC0233395

> *"Support identified that a full system reservation was active on the cluster... which prevented node allocation."*
> — INC0212085

> *"The failures were due to an active compute reservation (axonn_gb2) occupying many nodes from 10:00 to 20:00 on that day, which triggers the 'ReqNodeNotAvail' error."*
> — INC0217991

---

### 🧩 Why Long-Duration Jobs Are Especially Affected

Slurm's backfill scheduler will **not start a job if its walltime would extend past a reservation boundary** on the required nodes. So even if some nodes are technically free right now, if the job's requested walltime overlaps with an upcoming reservation or maintenance window, Slurm will refuse to start it. Large node-count jobs compound this because *all* requested nodes must be simultaneously available for the full duration.

---

### ✅ Diagnostic Steps

1. **Check active and upcoming reservations:**
   ```bash
   scontrol show reservations
   ```
   Look for reservations covering the `nid[...]` nodes listed in the error, and compare their `StartTime`/`EndTime` against your job's requested walltime.

2. **Inspect the job reason in detail:**
   ```bash
   scontrol show job <JOBID>
   ```
   Look for `Reason=ReqNodeNotAvail` and any mention of `Reserved for maintenance`.

3. **Check the system live status page** (e.g., https://www.nersc.gov/live-status/motd/) for announced maintenance windows.

---

### 🛠️ Resolution Options

| Option | Action |
|---|---|
| **Wait it out** | The job will start automatically once the reservation/maintenance window ends. No user action required. |
| **Reduce walltime** | If the requested walltime is longer than necessary, reducing it may allow the job to fit in the gap before the reservation starts. |
| **Use `--time-min`** | Submit with a minimum acceptable walltime so Slurm has more flexibility to backfill. |
| **Use checkpoint/restart** | Break the long job into shorter chained jobs that individually fit within available windows. This is the [recommended best practice](jobs/best-practices.md) for long-running simulations. |
| **Request a formal reservation** | If you need guaranteed, uninterrupted access to many nodes for a long duration, submit a [Reservation Request](https://nersc.servicenowservices.com/sp/?id=sc_cat_item&sys_id=1c2ac48f6f8cd2008ca9d15eae3ee4a5) with at least **1 week's notice**. |

---

### 📚 Sources
- **Tickets:** INC0212085, INC0212099, INC0217991, INC0233395 (`tickets` collection)
- **Docs:** `jobs/troubleshooting.md`, `jobs/reservations.md`, `jobs/best-practices.md` (`docs` collection)
````

### Reference Answer

Most likely explanation: an active full-system reservation temporarily prevents scheduler placement, so pending reason reflects node unavailability/reservation constraints.

Key clues:
- Pending reason references unavailable nodes.
- Request size/duration is large and sensitive to reservation windows.

Correct guidance:
- Check reservation/maintenance schedule and wait for window to clear.
- Re-evaluate queue reason after reservation ends.
- Keep constraints minimal unless strictly required.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional context and detailed guidance.
````

---

## 35. lang_sonnet_chroma_opt | ticket | borderline | INC0242061_account_recovery_username_mfa

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet_opt__claude_sonnet__c5902b01/ticket_cases/INC0242061_account_recovery_username_mfa/0/run.json`

### User Prompt

````text
During account recovery after organization/email updates, user is unsure of correct login identifier and cannot complete login despite receiving reset instructions.

What is the common failure mode?
````

### Model Answer

````text
## Common Failure Mode: Stale or Mismatched Login Identifier After Org/Email Update

The evidence from multiple ticket records and operational documentation consistently points to **one dominant failure mode**: the user's **registered email address on file is outdated or no longer valid**, causing the self-service password reset flow to silently fail or deliver instructions to an unreachable inbox — and the user simultaneously doesn't know which **username** to enter.

---

### 🔴 Root Cause Breakdown

| Factor | What Goes Wrong |
|---|---|
| **Old/expired email on record** | The reset email is sent to a defunct institutional address (e.g., post-graduation, post-org change). The user never receives it. |
| **Username confusion** | The password reset form requires both a **username** *and* the **registered email address** to match. After an org change, users often try their new email — which doesn't match the old record — causing the lookup to fail with: *"We are unable to find this username, email, and MFA token combination."* |
| **No secondary email fallback** | If no secondary email is registered, there is no alternate delivery path for the reset link. |
| **Self-service loop** | The user tries "Forgot password?" and "Forgot username?" repeatedly, both fail, and they receive no actionable feedback. |

---

### 📋 Evidence from Tickets

- **INC0213622**: *"Primary email had been withdrawn after graduation, preventing receipt of reset messages."* → Support updated the primary email and added a Gmail secondary.
- **INC0236960**: *"Password reset flow required the old email"* after an org/email change. → Support updated the IRIS profile email and issued a reset link.
- **INC0206040**: *"We are unable to find this username, email, and MFA token combination"* — root cause was an **inactive email on file** and an **expired password**.
- **INC0226020**: User was using an **incorrect username** and had **no secondary email** — both compounded the failure.

---

### ✅ Resolution Steps (Operator Action)

1. **Look up the user in IRIS** via ServiceNow's *"View User in Iris"* link.
2. **Update the primary email** to the user's new/active institutional address.
3. **Add a secondary email** (e.g., Gmail) as a fallback contact.
4. **Confirm the correct username** and communicate it directly to the user — it does not change with org/email updates.
5. **Send a password reset link** from the IRIS Profile tab → *"Reset Pwd Email"* button.
6. Instruct the user to complete the reset **on a laptop/desktop** (not mobile) to avoid browser caching issues.

---

### 📌 Key Takeaway

> **The failure is not the reset instructions themselves — it's that the email address on record no longer matches the user's current identity, and the user doesn't know their original username.** These two mismatches together cause the self-service flow to appear broken even when the system is working correctly.

*Sources: tickets `INC0213622`, `INC0236960`, `INC0226020`, `INC0206040`; docs `accounts/passwords.md`, `common-question-categories/index.md` (Account Support section).*
````

### Reference Answer

Most likely failure mode: wrong username format plus incomplete password reset and stale MFA token state.

Key clues:
- User attempts email-style login forms instead of account username.
- Reset completion email was not received, indicating reset did not finish.
- MFA failures continue until token flow is refreshed.

Correct guidance:
- Use canonical NERSC username for login.
- Confirm password reset completion email before retrying auth.
- Recreate/check MFA token if failures persist.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response provides a detailed analysis of the issue, focusing on username confusion and email updates. While it doesn't directly address the stale MFA token state, it offers relevant resolution steps. The response is well-structured and supported by evidence from ticket records.
````

---

## 36. lang_sonnet_chroma_opt | ticket | fail_or_skip | INC0240995_jupyter_404_502_spin_degradation

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_chroma_sonnet_opt__claude_sonnet__c5902b01/ticket_cases/INC0240995_jupyter_404_502_spin_degradation/0/run.json`

### User Prompt

````text
Jupyter intermittently returns 404/502 and kernels stop unexpectedly across the morning.

What is the most likely cause?
````

### Model Answer

````text
Based on the retrieved evidence across all three collections, here is a comprehensive analysis:

---

## Most Likely Cause: **Home Directory Over Quota**

The strongest pattern across multiple resolved tickets and official documentation points to **home directory quota exhaustion** as the primary culprit for intermittent 404/502 errors and unexpected kernel stops.

---

### Why This Fits Your Symptoms

| Symptom | How Quota Exhaustion Causes It |
|---|---|
| **404 Not Found** | JupyterHub cannot write utility/state files to `$HOME`; the hub proxy loses track of the server → returns 404 (INC0239149) |
| **502 Bad Gateway** | The notebook server fails to spawn or crashes mid-session because it can't write to `$HOME` → the proxy gets no response → 502 |
| **Kernels stop unexpectedly** | Kernels write connection files (e.g., `/tmp/jupyter-runtime/kernel-*.json`) and checkpoint files in `$HOME`; when `$HOME` is full, these writes fail and the kernel dies |
| **Intermittent / morning pattern** | Usage accumulates overnight (logs, conda caches, output files); the quota tip-over point is crossed in the morning as work resumes |

---

### Evidence from Tickets & Docs

- **INC0228983**: User got HTTP 500 + disk I/O errors in Jupyter — traced to home at **100.3% quota** (40.12 GiB / 40 GiB). Fixed by freeing space.
- **INC0211489**: Jupyter failures after environment change — home at **100.9% quota** (40.37 GiB / 40 GiB). Fixed by removing files.
- **INC0211510**: JupyterHub spawn failed with `Http 507 Insufficient Storage` — home directory over quota.
- **INC0206572**: Quota exceeded by hidden files — specifically `~/.conda/pkgs` and `~/.jupyter-*.log`.
- **Official docs** (`services/jupyter/how-to-guides.md`): *"If your home directory is over quota, JupyterLab will not be able to update utility files stored there, and will not work properly."* JupyterHub explicitly **detects quota overrun before launch** and halts with an error.

---

### Immediate Diagnostic Steps

**1. Check quota via SSH (since Jupyter may be unusable):**
```bash
ssh user@perlmutter.nersc.gov
showquota
```
Look for home directory at or above 100%.

**2. Find the space hogs:**
```bash
du -sh $HOME/.[!.]* $HOME/*   # hidden + visible dirs
du -csh $HOME/.conda/envs/* $HOME/.conda/pkgs
du -sh $HOME/.cache/pip
ls -lh $HOME/.jupyter-*.log
```

---

### Fix

Free space in `$HOME` — common culprits:

| Culprit | Fix |
|---|---|
| `~/.conda/pkgs` (package cache) | `conda clean -a` |
| Old conda environments | `conda env remove -n <env>` |
| Jupyter log files (`~/.jupyter-*.log`) | `rm ~/.jupyter-*.log` |
| Large data files | `mv bigdata $SCRATCH/` |
| pip cache | `python -m pip cache purge` |

Once under quota, restart the Jupyter server from the Hub Control Panel.

---

### Secondary Causes to Rule Out

If quota is **not** the issue, also check:
1. **Transient service outage** — check the [NERSC Outage Log](https://my.nersc.gov/outagelog-cs.php) and MOTD (INC0239149 showed a 404 caused by a platform-side outage, not the user).
2. **Stale browser cache/cookies** — a stale session token causes 404s; fix by clearing browser cache and logging in fresh (INC0236523).
3. **Corrupt kernel runtime files** in `/tmp/jupyter-runtime/` — resolved by full logout + browser cache clear.

> **Bottom line:** Run `showquota` over SSH first. In the majority of documented cases, home directory quota exhaustion is the root cause of this exact combination of symptoms.
````

### Reference Answer

Most likely cause: transient Spin/Jupyter backend degradation.

Key clues:
- Mixed 404/502 errors and intermittent recovery.
- Multiple users report similar timing.

Correct guidance:
- Treat as service incident first; retry after stabilization.
- Avoid immediate local environment changes unless issues persist post-recovery.
- Monitor center status for confirmation/resolution updates.

### Automated Judgment

- Status: `scored`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
The agent's response does not match the expected solution. It identifies a different root cause (home directory quota exhaustion) and provides different guidance, whereas the reference solution points to transient Spin/Jupyter backend degradation as the most likely cause and advises treating it as a service incident.
````

---

## 37. lang_gptoss_filesystem | qa | clear_pass | 44d3400b69bc

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/nersc_qa.v2/44d3400b69bc/0/run.json`

### User Prompt

````text
How does a user restore an accidentally deleted file from Home using snapshots?
````

### Model Answer

````text
**Answer**

A user can recover a file that was accidentally removed from their `$HOME` directory by copying it out of one of the automatic Home‑directory snapshots. The steps are:

1. **Enter the snapshot area**  
   ```bash
   cd $HOME/.snapshots
   ```

2. **List the available snapshots** (they are timestamped directories)  
   ```bash
   ls -F
   ```
   Example output: `snapshot.2024-03-15-12-00-00/  snapshot.2024-03-14-12-00-00/ …`

3. **Find the snapshot that contains the lost file**  
   You can look inside a snapshot with a normal `ls` or `find`. For example, to see the contents of the most recent snapshot:  
   ```bash
   ls -R snapshot.2024-03-15-12-00-00 | grep <filename>
   ```

4. **Copy the file back to your Home directory** (snapshots are read‑only, so you can only copy out)  
   ```bash
   cp snapshot.2024-03-15-12-00-00/path/to/your/file $HOME/path/to/your/file
   ```

5. **Verify the restore**  
   ```bash
   ls -l $HOME/path/to/your/file
   ```

**Key points from the documentation**

- Every directory in `$HOME` has a hidden `.snapshots` entry that holds a seven‑day history of the home directory.  
- The `.snapshots` directory is invisible to normal `ls`, `ls -a`, `find`, etc., but becomes visible when you `cd .snapshots`.  
- Snapshots are **read‑only**; you cannot modify or delete files inside them, only copy files out.  

(Excerpt from `docs/filesystems/global-home.md`:  
> “A *snapshot* capability is used to provide users a seven‑day history of their home directories. Every directory and sub‑directory in `$HOME` contains a `.snapshots` entry… Files can *only* be copied *out* of a snapshot.”)

**Next steps if the needed snapshot is older than 7 days**

If the file is not present in any of the listed snapshots, it has likely been purged (snapshots are kept for only seven days). In that case you would need to rely on any external backups you maintain or contact NERSC support for further assistance.
````

### Reference Answer

Answer: Navigate to the `.snapshot` directory inside the directory where the file was, choose the desired snapshot timestamp, and copy the file back to the original location.

Source doc: https://docs.nersc.gov/filesystems/home/

Section: Home FS

Source passage: To restore a file, navigate to the .snapshot directory, choose the snapshot with the desired timestamp, and copy the file back to its original location.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional helpful details.
````

---

## 38. lang_gptoss_filesystem | qa | borderline | 0481a3b31f19

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/nersc_qa.v2/0481a3b31f19/0/run.json`

### User Prompt

````text
Why is the Home filesystem not recommended for storing conda environments or large software stacks?
````

### Model Answer

````text
**Answer**

The Global HOME filesystem is intended only for small, user‑specific files (dotfiles, source code, configuration, etc.). It is **not recommended** for conda environments or other large software stacks because:

| Reason | Evidence from the documentation |
|--------|-----------------------------------|
| **Performance is tuned for small files** – HOME is mounted via DVS, which is optimized for compiling/linking, not for large, streaming I/O. | “The file system is optimized for small files and is suitable for compiling and linking executables. Global home directories are **not intended for large, streaming I/O**.” – *docs/filesystems/global‑home.md* |
| **Quota limits are very low** – Home quotas are only increased in “extremely unusual circumstances,” so a full conda environment can quickly exceed the space or inode limits. | “Quota increases in Global Homes are approved only in *extremely* unusual circumstances.” – *global‑home.md* |
| **Snapshots cannot store large data** – Home snapshots are read‑only and only allow copying files out; they are not a place to keep large binaries. | “Files cannot be created, deleted or edited in snapshots… Files can *only* be copied *out* of a snapshot.” – *global‑home.md* |
| **Backup responsibility remains with the user** – Although NERSC provides snapshots, they are limited to 7 days and are not a substitute for proper backup of large software. | “All NERSC users should backup important files on a regular basis… snapshots provide a seven‑day history of home directories.” – *global‑home.md* |

Because of these constraints, the recommended locations for conda environments or large software stacks are the high‑performance, high‑quota filesystems such as **$SCRATCH** (Perlmutter Scratch) or other project‑specific Lustre/GPFS filesystems, which are designed for large, I/O‑intensive workloads and have appropriate purge/backup policies.
````

### Reference Answer

Answer: Home is not tuned for high-performance parallel jobs. Common should be used for applications sourced by more than a dozen nodes, or software stacks with many small files like conda environments.

Source doc: https://docs.nersc.gov/filesystems/

Section: Home

Source passage: This file system is not tuned for high performance on parallel jobs: use the more optimized Common file system to store applications that need to be sourced by more than a dozen nodes at a time, or applications composed of several packages and small files such as conda environments.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response provides a detailed explanation of why HOME is not suitable for large software stacks, aligning with the reference solution's intent. However, it does not directly mention 'high-performance parallel jobs' or 'Common' filesystem as stated in the reference solution.
````

---

## 39. lang_gptoss_filesystem | qa | fail_or_skip | 001938cecc88

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/nersc_qa.v2/001938cecc88/0/run.json`

### User Prompt

````text
What SBATCH directive specifies the number of nodes for a job?
````

### Model Answer

````text
Error: Recursion limit of 32 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key.
For troubleshooting, visit: https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT
````

### Reference Answer

Answer: The `#SBATCH -N <number>` or `#SBATCH --nodes=<number>` directive specifies the number of nodes.

Source doc: https://docs.nersc.gov/jobs/

Section: Running Jobs

Source passage: Use #SBATCH -N <number> or --nodes=<number> to request a specific number of nodes.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 40. lang_gptoss_filesystem | ticket | clear_pass | INC0247364_jupyter_qos_walltime

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/ticket_cases/INC0247364_jupyter_qos_walltime/0/run.json`

### User Prompt

````text
My long-running work in a Perlmutter Jupyter session keeps stopping after about 5-6 hours.

Symptoms:
- Session is stable initially, then dies around the same elapsed runtime.
- This repeats across attempts.
- I am launching work through a Jupyter-backed interactive session.

What is the likely cause and how should I run this workload reliably?
````

### Model Answer

````text
**Likely cause** – the Jupyter service on Perlmutter runs under the **`jupyter` QOS**, which has a hard wall‑time limit of **6 hours**. When the allocation reaches that limit the interactive session is terminated, which is why your work consistently dies after ~5‑6 h.

*Evidence* (from the policy document referenced in the corpus):  

- File: `docs/jobs/policy.md` – the QOS table lists  

  ```
  | jupyter | 4 | 6 | … |
  ```  

  (max nodes = 4, **max time = 6 hrs**).  

  This is the QOS used by the NERSC Jupyter service, and the session is killed when the wall‑time expires.

---

### How to run the workload reliably

| Option | What to do | Why it helps |
|--------|------------|--------------|
| **Submit as a batch job** | Write a normal Slurm script (`#!/bin/bash … #SBATCH -q regular … #SBATCH -t 48:00 …`) and submit with `sbatch`. | Batch jobs use the `regular` (or another appropriate) QOS, which can run up to 48 h (or longer) and is not limited to the 6‑h Jupyter wall‑time. |
| **Use an interactive allocation with a longer QOS** | Request an interactive allocation with `salloc` (or `srun --pty`) using a QOS that allows the needed wall‑time, e.g.: <br>`salloc -N 1 -q regular -t 12:00 -C gpu -A <project>` <br>Then start Jupyter/Lab inside that allocation (`module load jupyter; jupyter lab …`). | The interactive allocation inherits the QOS you request, so you can get 12 h (or more) instead of the 6‑h limit. |
| **Checkpoint / split the work** | Add checkpointing to your code (e.g., write intermediate results to `/pscratch` every hour) and restart from the last checkpoint in a new session. | If you must stay in the Jupyter service, breaking the job into ≤ 6 h chunks avoids the forced termination. |
| **Use NERSC’s “Jupyter on compute nodes”** | Launch Jupyter from a batch allocation (as above) rather than the hosted Jupyter service. | This runs Jupyter inside a regular batch job, so you benefit from the longer wall‑time of that job. |

#### Quick recipe for a long‑running Jupyter workflow

```bash
# 1. Allocate resources (e.g., 1 GPU node for 24 h)
salloc -N 1 -C gpu -q regular -t 24:00 -A myproject

# 2. Inside the allocation, start JupyterLab
module load jupyter
jupyter lab --no-browser --port=8888 &
# 3. Open an SSH tunnel from your laptop
ssh -N -L 8888:login-node:8888 $USER@perlmutter.nersc.gov
# 4. Open http://localhost:8888 in your browser
```

Now your notebook runs under the `regular` QOS and will not be killed at the 6‑hour mark.

---

**Bottom line:** The 5‑6 hour termination is the expected behavior of the `jupyter` QOS. To run long‑running workloads, submit them as batch jobs or use an interactive allocation with a QOS that permits a longer wall‑time, and optionally add checkpointing if you must stay within the hosted Jupyter service.
````

### Reference Answer

Most likely cause: hitting the Jupyter QOS walltime limit (about 6 hours), not an application crash.

Key clues:
- Failures happen at a consistent elapsed time (5-6 hours).
- Behavior is tied to Jupyter/interactive session mode.
- NERSC QOS policy for Jupyter has a shorter walltime cap than regular batch usage.

Correct guidance:
- Treat Jupyter sessions as interactive/dev workflows, not long production runs.
- Move long computations to `sbatch` in an appropriate non-Jupyter QOS with suitable walltime.
- Keep checkpoints so interrupted interactive sessions can resume work.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional details and alternatives for resolving the issue.
````

---

## 41. lang_gptoss_filesystem | ticket | borderline | INC0240630_vasp_nccl_rpath_behavior

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/ticket_cases/INC0240630_vasp_nccl_rpath_behavior/0/run.json`

### User Prompt

````text
I compiled VASP against `nccl/2.18.3-cu12` on Perlmutter. If I later `module load nccl/2.24.3` before running, which NCCL does VASP actually use?

Context:
- I am trying to understand whether runtime module changes override compile-time choices.
- I also want to avoid runtime hangs seen with some NCCL versions.

What is the likely behavior and recommended practice?
````

### Model Answer

````text
**Answer**

VASP is linked to NCCL at **link‑time**, but the actual library that is loaded at run time is the one the dynamic loader finds in the current `LD_LIBRARY_PATH` (or an RPATH baked into the executable).  

- If VASP was built **against a shared NCCL library** (`libnccl.so`) without an explicit RPATH, the loader will pick the first `libnccl.so` it finds when the program starts.  
- Loading a different NCCL module (`module load nccl/2.24.3`) changes `LD_LIBRARY_PATH` (and possibly `LD_PRELOAD`), so the **runtime version overrides the compile‑time version**.  
- If VASP was built **statically** (`-static` or with `libnccl.a`) or with an RPATH that points to the exact NCCL installation used during compilation, the runtime module will have no effect; the binary will always use the compiled‑in version.

Because most NERSC builds (including the typical Perlmutter module‑based workflow) use shared libraries, the common situation is:

> **VASP will run with the NCCL version that is currently loaded in the environment, not the one that was present when you compiled it.**

---

### Why this matters for hangs

Different NCCL releases can have ABI changes, bug fixes, or regressions. If you compile with 2.18.3 but run with 2.24.3, you may encounter:

- Mismatched symbols (if the API changed) → immediate load failure.
- Subtle runtime hangs or deadlocks (common when internal algorithms differ).

Thus the observed hangs are likely caused by the version mismatch.

---

### Recommended practice

| Step | Reason |
|------|--------|
| **1. Keep compile‑time and run‑time NCCL versions identical** | Guarantees ABI compatibility and reproduces the tested configuration. |
| **2. Use `module purge` before loading the NCCL module you intend to use** | Prevents leftover paths from a previous module from contaminating the environment. |
| **3. Verify the library that will be loaded** | Run `ldd $(which vasp)` (or the full path to the VASP executable) after loading the module; check the path shown for `libnccl.so`. |
| **4. (Optional) Embed an RPATH at compile time** | Add `-Wl,-rpath,$NCCL_ROOT/lib` (or the module’s `$EBROOTNCCL/lib`) to the link flags. This forces the binary to use that exact library regardless of later `LD_LIBRARY_PATH` changes. |
| **5. Test with a small MPI/NCCL benchmark** | Before large runs, execute a short `mpirun -n 2 vasp` or an NCCL test program to confirm no hangs. |
| **6. Document the NCCL version in your job script** | E.g., `#SBATCH --export=ALL,NCCL_VERSION=2.18.3` and load the same module in the script. |

---

### Quick sanity check you can run on Perlmutter

```bash
module purge
module load nccl/2.24.3  # or the version you plan to run
module load vasp          # loads the VASP module you compiled
ldd $(which vasp) | grep libnccl
```

The output should show something like:

```
libnccl.so.2 => /global/cfs/cdirs/modulefiles/nccl/2.24.3/lib/libnccl.so.2 (0x00007f...)
```

If it points to a different path (e.g., the 2.18.3 directory), you are still picking up the old version.

---

**Bottom line:** In the typical shared‑library build, the NCCL module you load **at runtime determines the NCCL library VASP uses**. Keep the versions aligned, purge modules before loading, and verify with `ldd` to avoid the hangs you’ve observed.
````

### Reference Answer

Most likely behavior: VASP keeps using the NCCL version encoded in its runtime search path (rpath) from build time, not whichever NCCL module is loaded later.

Key clues:
- Question concerns mismatch between compile-time NCCL and runtime loaded module.
- VASP builds commonly embed rpath entries in `makefile.include`.
- Runtime hangs are version-dependent, so deterministic library selection matters.

Correct guidance:
- Treat NCCL choice as a build-time decision for VASP unless you intentionally alter linking/rpath behavior.
- Keep build and run environments aligned and validate with library inspection tools.
- If changing NCCL version is required, rebuild and re-test rather than assuming a runtime module swap will safely override dependencies.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The response is comprehensive and provides useful guidance on ensuring NCCL version compatibility with VASP. It could be improved by more directly addressing the likelihood of VASP using the NCCL version from build time when an RPATH is present.
````

---

## 42. lang_gptoss_filesystem | ticket | fail_or_skip | INC0240565_lammps_allegro_mkl_libpath

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/ticket_cases/INC0240565_lammps_allegro_mkl_libpath/0/run.json`

### User Prompt

````text
I am testing a custom LAMMPS/Allegro container on Perlmutter for a NequIP/Allegro workflow and now see:

lmp: error while loading shared libraries: libmkl_intel_lp64.so.2: cannot open shared object file: No such file or directory

Context:
- The model/container version alignment issue was already being addressed with a newly built image.
- This new error appears immediately at process startup before the simulation proceeds.
- I am launching through Shifter.

What is the most likely cause and fix?
````

### Model Answer

````text
Error: Error: EISDIR: illegal operation on a directory, read
````

### Reference Answer

Most likely cause: the container has the MKL library installed but its path is missing from runtime library search configuration (`LD_LIBRARY_PATH`).

Key clues:
- Error is a dynamic loader failure for a specific shared library (`libmkl_intel_lp64.so.2`).
- Failure happens at launch, before model physics/input validation.
- The issue appears after moving to a newly built container variant.

Correct guidance:
- Use the updated container image where the MKL path fix is already applied.
- If using an intermediate image, prepend the MKL lib directory to `LD_LIBRARY_PATH` inside the container (for example `/opt/intel/oneapi/mkl/2025.2/lib`).
- Re-run and confirm the launcher gets past shared-library loading before debugging any remaining model/version compatibility issues.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---

## 43. lang_sonnet_filesystem | qa | clear_pass | b8a1b25b72f7

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_sonnet__claude_sonnet__fae319fc/nersc_qa.v2/b8a1b25b72f7/0/run.json`

### User Prompt

````text
Can Shifter containers access NERSC filesystems like $SCRATCH and CFS?
````

### Model Answer

````text
I now have comprehensive documentation. Here is a complete answer:

---

## Yes — Shifter Containers Have Full Access to NERSC Filesystems

Shifter containers at NERSC can access `$SCRATCH`, the Community File System (CFS), `$HOME`, and other NERSC filesystems. Here's how it works:

---

### Automatic Access (No Extra Configuration Needed)

By default, Shifter **automatically mounts the major NERSC filesystems** into the container. Your environment variables (including `$SCRATCH`) are also passed through from the calling process into the container, so code inside the container can reference them directly.

> **Key caveat:** Images are mounted **read-only**, so all output must go to a NERSC filesystem (e.g., `$SCRATCH` or CFS), not to paths inside the image.

---

### Explicit Volume Mounting

You can also **explicitly mount** specific directories using the `--volume` flag, which is useful for mapping a NERSC path to a custom path inside the container:

```slurm
# Mount $SCRATCH to /output inside the container
#SBATCH --volume="/pscratch/sd/<first_letter>/<username>:/output"
```

For **multiple mounts**, separate them with a semicolon:

```slurm
#SBATCH --volume="/global/cfs/cdirs/mpcc:/output;/global/cfs/cdirs/mpcc:/input"
```

> ⚠️ **Important:** When using `#SBATCH --volume`, **do not use environment variables** like `$SCRATCH` or `$HOME` — they won't be resolved at submission time. Use the full absolute path (e.g., `/pscratch/sd/s/username`).

---

### CFS-Specific Requirement

Community File System (CFS) **must be accessed via its full path** inside a Shifter container:

```
/global/cfs/cdirs/<project>/
```

The shortcut `/cfs/` does **not** work inside Shifter.

---

### HOME Filesystem — Extra Step Required

To mount from `$HOME`, you must grant execute (`x`) permission to the `nobody` user on your top-level `$HOME` directory and any subdirectories you want to mount. See the [Shifter FAQ](docs/development/containers/shifter/faq-troubleshooting.md) for details on the "Invalid Volume Map" error.

---

### Summary Table

| Filesystem | Accessible in Shifter? | Notes |
|---|---|---|
| `$SCRATCH` (`/pscratch/...`) | ✅ Yes | Use full path in `#SBATCH --volume` |
| CFS (`/global/cfs/...`) | ✅ Yes | Must use `/global/cfs/` prefix, not `/cfs/` |
| `$HOME` | ✅ Yes | Requires granting `x` permission to `nobody` |
| Inside the image | ❌ Read-only | Cannot write to image paths |

**Source:** `docs/development/containers/shifter/how-to-use.md`
````

### Reference Answer

Answer: Yes, NERSC filesystems including scratch, home, and CFS are automatically mounted inside Shifter containers.

Source doc: https://docs.nersc.gov/software/shifter/

Section: Shifter Containers

Source passage: NERSC file systems, including home, scratch, and Community, are automatically mounted and accessible inside Shifter containers.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional details.
````

---

## 44. lang_sonnet_filesystem | qa | borderline | aa2a81b8bc73

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_sonnet__claude_sonnet__fae319fc/nersc_qa.v2/aa2a81b8bc73/0/run.json`

### User Prompt

````text
How many A100 GPUs are on each GPU node on Perlmutter?
````

### Model Answer

````text
Each GPU node on Perlmutter has **4 NVIDIA A100 GPUs**.

Specifically, there are two types of GPU nodes:

| Node Type | # of Nodes | GPUs per Node | GPU Memory |
|---|---|---|---|
| GPU (standard) | 1,536 | 4x NVIDIA A100 | 40 GB HBM2 each |
| GPU (large memory) | 256 | 4x NVIDIA A100 | 80 GB HBM2e each |

Both variants have the same count of **4 A100 GPUs per node**, connected via 4 third-generation NVLink connections between each pair of GPUs. The nodes also feature a single AMD EPYC 7763 (Milan) CPU with 64 cores and 256 GB of DDR4 DRAM.

*Source: `/pscratch/sd/s/sfarrell/athos/workspace/file_retrieval_corpus/docs/systems/perlmutter/architecture.md`*
````

### Reference Answer

Answer: Each GPU node on Perlmutter has four NVIDIA A100 40 GB GPUs.

Source doc: https://docs.nersc.gov/systems/perlmutter/architecture/

Section: Perlmutter Architecture

Source passage: Each Perlmutter GPU node is equipped with four NVIDIA A100 40 GB Tensor Core GPUs.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response correctly states that there are 4 NVIDIA A100 GPUs per node on Perlmutter but omits the detail that they are '40 GB' GPUs. Additional context provided supports the accuracy of the count and type of GPUs.
````

---

## 45. lang_sonnet_filesystem | qa | fail_or_skip | 864edf504e6c

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_sonnet__claude_sonnet__fae319fc/nersc_qa.v2/864edf504e6c/0/run.json`

### User Prompt

````text
What is the maximum wall clock time for a regular job on Perlmutter?
````

### Model Answer

````text
The answer is clear from the official policy documentation.

## Maximum Wall Clock Time for a Regular Job on Perlmutter: **48 hours**

This applies to **both** Perlmutter GPU and Perlmutter CPU nodes in the `regular` QOS:

| System | QOS | Max Time |
|---|---|---|
| Perlmutter GPU | regular | **48 hours** |
| Perlmutter CPU | regular | **48 hours** |

**Key details about the `regular` QOS:**
- **No node limit** is imposed (though not all projected nodes may be available at any given time).
- **Priority:** Medium
- **QOS Factor:** 1 (standard charge rate)
- **Submit limit:** 5,000 jobs
- Nodes are **exclusively** allocated to the job.

**Source:** `docs/jobs/policy.md` — QOS Limits and Charges tables for Perlmutter GPU and CPU.
````

### Reference Answer

Answer: The maximum wall clock time for a regular queue job on Perlmutter is 24 hours.

Source doc: https://docs.nersc.gov/jobs/policy/

Section: Job Policy

Source passage: Jobs in the regular queue on Perlmutter have a maximum wall clock time of 24 hours.

### Automated Judgment

- Status: `scored`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
The agent's response states that the maximum wall clock time for a regular job on Perlmutter is 48 hours, which contradicts the reference solution that states it is 24 hours.
````

---

## 46. lang_sonnet_filesystem | ticket | clear_pass | INC0242753_ssh_login_target_and_otp_format

- Judge score: `100`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_sonnet__claude_sonnet__fae319fc/ticket_cases/INC0242753_ssh_login_target_and_otp_format/0/run.json`

### User Prompt

````text
SSH login fails after trying legacy hostnames/procedures, and user is unsure about current auth format.

Context:
- Attempts used old target hostnames.
- Prompt expects combined password + OTP entry.

What is the correct login method?
````

### Model Answer

````text
Here is a complete, authoritative answer based on the official NERSC documentation (`docs/connect/index.md` and `docs/connect/mfa.md`):

---

## ✅ Correct SSH Login Method for NERSC (Perlmutter)

### 1. Use the Correct Hostname

Legacy hostnames no longer work. The **current, valid hostnames** for Perlmutter are:

```
perlmutter.nersc.gov
```
or
```
saul.nersc.gov
```

**SSH command:**
```bash
ssh <your_nersc_username>@perlmutter.nersc.gov
```

---

### 2. Authentication: Password + OTP (Combined Entry)

NERSC requires **Multi-Factor Authentication (MFA)**. When prompted, you will see:

```
Password + OTP:
```

You must type your **NERSC password immediately followed by your 6-digit OTP** — all in one string, with **no space** between them.

**Example:**
- NERSC password: `iL0ve_Burrit0$`
- OTP from authenticator app: `015691`
- **What you type:** `iL0ve_Burrit0$015691`

> ⚠️ Do NOT type a space between the password and OTP, even though the authenticator app may display the OTP with a space (e.g., `015 691`).

---

### 3. Optional: Use `sshproxy` for Passwordless Login (Up to 24 Hours)

To avoid re-entering your password+OTP every session, use the **`sshproxy`** tool:

```bash
sshproxy -u <your_nersc_username>
# Enter Password+OTP once
```

This generates a temporary SSH key (`~/.ssh/nersc`) valid for 24 hours. Then log in with:

```bash
ssh -i ~/.ssh/nersc <your_nersc_username>@perlmutter.nersc.gov
```

Or configure `~/.ssh/config` to use it automatically:

```
Host perlmutter*.nersc.gov saul*.nersc.gov dtn*.nersc.gov
    User <your_nersc_username>
    IdentityFile ~/.ssh/nersc
    IdentitiesOnly yes
    ForwardAgent yes
```

---

### 4. Common Login Failure Causes

| Symptom | Likely Cause | Fix |
|---|---|---|
| "Access Denied" / "Permission Denied" | Wrong username (local vs. NERSC) | Use `ssh <nersc_username>@perlmutter.nersc.gov` |
| "Too many authentication failures" | Too many SSH keys in agent | Run `ssh-add -D`, then retry |
| Login fails repeatedly | Account locked from failed attempts | Log into [Iris](https://iris.nersc.gov) → Profile → Unlock Account |
| OTP not working | Expired `sshproxy` key silently falls back to MFA prompt | Re-run `sshproxy` to get a fresh key |

---

### 📚 Sources
- `docs/connect/index.md` — SSH connection details and troubleshooting
- `docs/connect/mfa.md` — MFA setup and Password+OTP usage
````

### Reference Answer

Most likely issue: outdated target host + incorrect MFA input workflow.

Key clues:
- Attempt used legacy/decommissioned system hostname.
- Prompt expects concatenated password+OTP (no separator), timed correctly.

Correct guidance:
- Use current login endpoint (for example `perlmutter.nersc.gov`) and correct username.
- At prompt, enter password immediately followed by current OTP code, then submit before OTP rollover.
- Avoid mixing old system names/procedures from retired platforms.

### Automated Judgment

- Status: `scored`
- Score: `100.0`
- Pass: `True`

Rationale:

````text
The agent's response perfectly matches the expected solution and provides additional helpful information.
````

---

## 47. lang_sonnet_filesystem | ticket | borderline | INC0242061_account_recovery_username_mfa

- Judge score: `80`
- Judge pass: `pass`
- Judgment status: `scored`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_sonnet__claude_sonnet__fae319fc/ticket_cases/INC0242061_account_recovery_username_mfa/0/run.json`

### User Prompt

````text
During account recovery after organization/email updates, user is unsure of correct login identifier and cannot complete login despite receiving reset instructions.

What is the common failure mode?
````

### Model Answer

````text
The ticket evidence is clear and consistent across multiple incidents. Here is the definitive answer:

---

## Common Failure Mode: **Username/Email Mismatch Causing "Username Not Found" Error**

The most common failure mode during account recovery after an organization or email update is that the **login identifier the user is attempting (username, email, or MFA token combination) no longer matches what is on record** in the NERSC Iris portal. This causes the password-reset workflow to silently fail with the error:

> *"We are unable to find this username, email and MFA token combination."*

### Why It Happens

When a user changes affiliation, email address, or phone number — but the **account record in Iris is not updated simultaneously** — the recovery workflow cannot locate the account. The user receives reset instructions (e.g., a reset link email) but cannot complete login because they are entering an old or mismatched identifier.

### Specific Failure Patterns Seen in Tickets

| Ticket | Failure Detail |
|---|---|
| **INC0203637** | Primary email on account was incorrect/outdated; username+email+MFA lookup failed. User had to correct the email on the account before the reset worked. |
| **INC0205401** | Lost MFA authenticator + outdated contact info → "username not found" error; new account creation blocked because username already existed. |
| **INC0207540** | User forgot username entirely after org change and attempted to create a new account, only to be told the email was already associated with an existing account. |
| **INC0196131** | Affiliation, email, and phone all changed simultaneously, leaving the user locked out with no valid MFA or password path. |

### Resolution Steps (from tickets)

1. **Support verifies identity** via ORCID ID or other out-of-band confirmation.
2. **Contact information (email, phone, affiliation) is updated** in the Iris account record.
3. **MFA is temporarily disabled** by support to remove that barrier.
4. A **fresh password-reset link is emailed** to the now-correct address.
5. User resets password (must be ≥14 characters) and re-enables MFA.
6. Note: **password propagation can take up to 4 hours** after reset.

### Key Takeaway

The root cause is **stale or mismatched account metadata** — the Iris portal's lookup requires an exact match of username + email + MFA token. Any one of these being out of sync after an org/email change will block recovery. Users should always update their Iris account details *before* losing access, and support should proactively update contact info as the first step in any recovery ticket.
````

### Reference Answer

Most likely failure mode: wrong username format plus incomplete password reset and stale MFA token state.

Key clues:
- User attempts email-style login forms instead of account username.
- Reset completion email was not received, indicating reset did not finish.
- MFA failures continue until token flow is refreshed.

Correct guidance:
- Use canonical NERSC username for login.
- Confirm password reset completion email before retrying auth.
- Recreate/check MFA token if failures persist.

### Automated Judgment

- Status: `scored`
- Score: `80.0`
- Pass: `True`

Rationale:

````text
The agent's response provides a comprehensive analysis of the issue and relevant resolution steps, although it does not perfectly match the reference solution's concise identification of the failure mode and guidance.
````

---

## 48. lang_sonnet_filesystem | ticket | fail_or_skip | INC0241472_jupyter_stuck_login_load

- Judge score: `0`
- Judge pass: `fail`
- Judgment status: `skipped_execution_status`
- Run path: `results/cug_m4/athos/cug_lang_filesystem_sonnet__claude_sonnet__fae319fc/ticket_cases/INC0241472_jupyter_stuck_login_load/0/run.json`

### User Prompt

````text
A JupyterHub server on a login node gets stuck in `closing` and cannot be stopped; later new servers also become inaccessible.

Context:
- I was running heavy troubleshooting commands/processes on a login node.
- Logging out/in did not clear the stuck state.

What is the likely root cause and fix?
````

### Model Answer

````text
Error: Recursion limit of 32 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key.
For troubleshooting, visit: https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT
````

### Reference Answer

Most likely cause: excessive user process load on login node prevented JupyterHub control actions from reaching/stopping the server.

Key clues:
- Server remains in prolonged stopping state.
- Login-node pressure is high from user processes.
- Manual process cleanup restores hub control behavior.

Correct guidance:
- Move compute-heavy or memory-heavy work off login nodes to compute allocations.
- Kill/reduce runaway login-node processes, then retry server stop/start.
- Use Jupyter on compute resources for substantial workloads.

### Automated Judgment

- Status: `skipped_execution_status`
- Score: `0.0`
- Pass: `False`

Rationale:

````text
Skipped: execution status=execution_error.
````

---
