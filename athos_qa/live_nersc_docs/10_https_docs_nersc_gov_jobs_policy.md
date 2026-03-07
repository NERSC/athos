# Source: https://docs.nersc.gov/jobs/policy/

## QOSes and Charges ¶

This page details the QOS ("Quality of Service") and usage policies for jobs run at NERSC. Examples for each type of Slurm job are available.
When a job runs on a NERSC supercomputer, charges accrue against one of the user's projects. The unit of accounting for these charges is the "Node Hour", based on the performance of the nodes on Perlmutter. The total number of charged hours for a job is a function of:
the number of nodes and the walltime used by the job,
the QOS of the job, and
the "charge factor" for the system upon which the job was run.
Job charging policies, including the intended use of each QOS, are outlined in more detail under "Policies" . This page summarizes the limits and charges applicable to each QOS.

## Selecting a QOS ¶

Jobs are submitted to different QOSes depending on the QOS constraints and the user's desired outcomes. Each QOS option corresponds to a "Quality of Service" (QOS): Each QOS has a different service level in terms of priority, run and submit limits, walltime limits, node-count limits, and cost.
Most jobs are submitted to the "regular" QOS, but some workflows have requirements outside of the regular QOS or can make use of other discounted QOSes.
Note
The "debug" QOS is the default QOS on Perlmutter and will be applied to any job for which a QOS is not specified.
All jobs submitted to the Slurm scheduler end up in the same queue, regardless of the QOS used for the job. A job's QOS determines at what point in the priority-ordered queue the job will enter.
One analogy for the job queue is the line waiting to board a ride at an amusement park. Some visitors wait in the usual line to board the ride while others purchase higher-cost passes which place them closer to the front of the line, but all visitors eventually end up on the same ride.
Job queue wait time can also be thought of in terms of the amusement park analogy. Just like a visitor may wait in line for hours to board a ride which only lasts several minutes, batch jobs may wait in the queue for much longer than a job's maximum allowable runtime.

## Assigning Charges ¶

Users who are members of more than one project can select which one should be charged for their jobs by default. In Iris , under the "Compute" tab in the user view, select the project you wish to make default.
To charge to a non-default project, use the -A projectname flag in Slurm, either in the Slurm directives preamble of your script, e.g.,
-A projectname
#SBATCH -A myproject
#SBATCH -A myproject
or on the command line when you submit your job, e.g., sbatch -A myproject ./myscript.sl .
sbatch -A myproject ./myscript.sl
Warning
For users who are members of multiple NERSC projects, charges are made to the default project, as set in Iris , unless the #SBATCH --account=<NERSC project> flag has been set.
#SBATCH --account=<NERSC project>

## Calculating Charges ¶

The cost of a job is computed in the following manner: $$ \text{walltime in hours} \times \text{number of nodes} \times \text{QOS factor} \times \text{charge factor} $$.
Example
The charge for a job that runs for 240 minutes on 3 CPU nodes in the preempt QOS (QOS factor of 0.5) would be calculated $$ \frac{240\ \text{mins}}{60\ \text{min/hr}} \times 3\ \text{nodes} \times 0.5 \times 1\ \text{charged-hours/node-hour} = 4 \times 3 \times 0.5 \times 1 = 6.0\ \text{charged hours}.$$
Example
A job which ran for 35 minutes on 3 GPU nodes on Perlmutter with the regular QOS would be charged: $$ \frac{35}{60}\ \text{hours} \times 3\ \text{nodes} \times 1 = 1.75\ \text{charged hours} $$
Note
Jobs in the "shared" QOS are only charged for the fraction of the node used.
Example
A job which ran for 10 hours on 2 GPUs in the shared QOS on Perlmutter GPU would be charged: $$ 10\ \text{hours} \times (2 \text{GPUs}/4) \times 1 = 5\ \text{charged hours} $$
Note
Jobs are charged according to the resources they made unavailable for other jobs, i.e., the number of nodes reserved (regardless of use) and the actual walltime used (regardless of the specified limit).

## Charge Factors ¶

Charge factors on Perlmutter are based on the performance of the Perlmutter nodes and are therefore equal to one. Future systems may have different charge factors.
Note
Perlmutter GPU and CPU allocations are separate pools that can be used only on the respective resource and cannot be exchanged.

## QOS Cost Factor: Charge Multipliers and Discounts ¶

A job's QOS cost factor (CF) is a function of which QOS it is run in.

## Big Job Discount ¶

Perlmutter GPU jobs in the regular QOS using 128 or more nodes are charged at a 50% discount. Perlmutter CPU jobs in the regular QOS using 256 or more nodes are also discounted by 50%.

## QOS Limits and Charges ¶


## Perlmutter GPU ¶

The "debug" QOS is the default.
The "debug" QOS is the default.
Nodes allocated by a "regular" QOS job are exclusively used by the job.
Nodes allocated by a "regular" QOS job are exclusively used by the job.
GPU jobs in the shared QOS may request 1 or 2 GPUs and will be allocated a corresponding 16 CPU cores and 64 GB RAM or 32 CPU cores and 128 GB RAM, respectively.
GPU jobs in the shared QOS may request 1 or 2 GPUs and will be allocated a corresponding 16 CPU cores and 64 GB RAM or 32 CPU cores and 128 GB RAM, respectively.
shared
NERSC's Jupyter service uses the jupyter QOS to start JupyterLab on compute nodes. Other uses of the QOS are currently not authorized, and the QOS is monitored for unauthorized use.
NERSC's Jupyter service uses the jupyter QOS to start JupyterLab on compute nodes. Other uses of the QOS are currently not authorized, and the QOS is monitored for unauthorized use.
jupyter
Jobs in the "preempt" QOS must request a minimum of 2 hours of walltime, and these jobs are charged for a minimum of 2 hours of walltime. Preemptible jobs are subject to preemption after two hours. Jobs can be automatically requeued after preemption using the --requeue sbatch flag; see the Preemptible Jobs section for details.
Jobs in the "preempt" QOS must request a minimum of 2 hours of walltime, and these jobs are charged for a minimum of 2 hours of walltime. Preemptible jobs are subject to preemption after two hours. Jobs can be automatically requeued after preemption using the --requeue sbatch flag; see the Preemptible Jobs section for details.
--requeue
Jobs may run on the "standard" Perlmutter GPU nodes or on the subset of GPU nodes which have double the GPU-attached memory. To specifically request these higher-bandwidth memory nodes, use -C gpu&hbm80g in your job script instead of -C gpu . Jobs with this constraint must use 256 or fewer nodes. To specifically request the "standard" Perlmutter GPU nodes, use -C gpu&hbm40g in your job script.
Jobs may run on the "standard" Perlmutter GPU nodes or on the subset of GPU nodes which have double the GPU-attached memory. To specifically request these higher-bandwidth memory nodes, use -C gpu&hbm80g in your job script instead of -C gpu . Jobs with this constraint must use 256 or fewer nodes. To specifically request the "standard" Perlmutter GPU nodes, use -C gpu&hbm40g in your job script.
-C gpu&hbm80g
-C gpu
-C gpu&hbm40g
Specific GPU requests on the command line
If you are submitting a job from the command line (e.g., via salloc ) which uses one of the memory-specific GPU constraints, you will need to specify the constraint within quotation marks (e.g., -C "gpu&hbm80g" ) so that the ampersand in the constraint is not interpreted as a shell symbol.
salloc
-C "gpu&hbm80g"

## Perlmutter CPU ¶

The "debug" QOS is the default.
The "debug" QOS is the default.
Nodes allocated by a "regular" QOS job are exclusively used by the job.
Nodes allocated by a "regular" QOS job are exclusively used by the job.
NERSC's Jupyter service uses the "jupyter" QOS to start JupyterLab on compute nodes. Other uses of the QOS are currently not authorized, and the QOS is monitored for unauthorized use.
NERSC's Jupyter service uses the "jupyter" QOS to start JupyterLab on compute nodes. Other uses of the QOS are currently not authorized, and the QOS is monitored for unauthorized use.
Even though there is no node limit for the regular QOS, not all of the projected 3072 nodes are available today. Please check the state of the nodes in the regular QOS with sinfo -s -p regular_milan_ss11
Even though there is no node limit for the regular QOS, not all of the projected 3072 nodes are available today. Please check the state of the nodes in the regular QOS with sinfo -s -p regular_milan_ss11
sinfo -s -p regular_milan_ss11
Jobs in the "preempt" QOS must request a minimum of 2 hours of walltime, and these jobs are charged for a minimum of 2 hours of walltime. Preemptible jobs are subject to preemption after two hours. Jobs can be automatically requeued after preemption using the --requeue sbatch flag; see the Preemptible Jobs section for details.
Jobs in the "preempt" QOS must request a minimum of 2 hours of walltime, and these jobs are charged for a minimum of 2 hours of walltime. Preemptible jobs are subject to preemption after two hours. Jobs can be automatically requeued after preemption using the --requeue sbatch flag; see the Preemptible Jobs section for details.
--requeue

## Perlmutter Login ¶


## Discounts ¶

Several QOSes offer reduced charging rates:
The "preempt" QOS is charged 50% of the "regular" QOS on CPU nodes and 25% of "regular" QOS on GPU nodes, with a minimum walltime of two hours guaranteed. Jobs in the "preempt" QOS are charged for a minimum of 2 hours of walltime, regardless of actual job runtime.
The "overrun" QOS is free of charge and is only available to projects that are out of allocation time. Please refer to the overrun section for more details.
Batch job submission is not enabled; jobs must be submitted via salloc . ↩ ↩
Batch job submission is not enabled; jobs must be submitted via salloc . ↩ ↩
salloc
Shared jobs are only charged for the fraction of the node resources used. ↩ ↩ ↩ ↩
Shared jobs are only charged for the fraction of the node resources used. ↩ ↩ ↩ ↩
Jobs in the "preempt" QOS are charged for a minimum of 2 hours of walltime, regardless of actual job runtime, and "preempt" QOS jobs must request a walltime of at least 2 hours. ↩ ↩ ↩ ↩
Jobs in the "preempt" QOS are charged for a minimum of 2 hours of walltime, regardless of actual job runtime, and "preempt" QOS jobs must request a walltime of at least 2 hours. ↩ ↩ ↩ ↩
The charge factor for premium jobs is 2 until a project has used 20 percent of its allocation on premium jobs. After that point, the charge factor increases to 4. ↩ ↩ ↩
The charge factor for premium jobs is 2 until a project has used 20 percent of its allocation on premium jobs. After that point, the charge factor increases to 4. ↩ ↩ ↩