# Source: https://docs.nersc.gov/jobs/scheduling/

## Job Scheduling ¶

NERSC uses the Slurm workload manager to handle scheduling of user jobs. NERSC's goals when scheduling jobs are to maximize throughput while keeping utilization as high as possible. When scheduling jobs, the batch system considers the priority, size (i.e. number of nodes), and requested wall time.

## Priority and Aging ¶

Slurm uses a value called priority to determine which jobs should be scheduled next. Priority is a measure of how long a job has been waiting in the queue.

## Starting Priority ¶

Different QOSes at NERSC can have different starting priority. For instance, jobs submitted to the interactive QOS have a higher starting priority than jobs submitted to regular , and jobs submitted to overrun have a much lower starting priority.
interactive
regular
overrun
Slurm won't schedule a start time for a job until it reaches a threshold priority (more on this in the Scheduling Algorithms section ) which makes the starting priority important. As an example, setting a large starting priority for the interactive QOS means those jobs will be very likely to get resources immediately.
interactive

## Aging ¶

The process of increasing the prioity value over time is called aging. At NERSC, jobs age in priority at a rate of 1 / minute.
Only two jobs per user age. This is done to reduce load on the scheduler and to allow an even distribution of resources across users and projects. This does not mean that only two jobs per user will ever be running at a time as Slurm has a scheduling algorithm that will harvest unaged jobs that can be run immediately (more on this in the Scheduling Algorithms section ).

## Scheduling Algorithms ¶

Slurm uses two algorithms to schedule jobs. The "immediate scheduler" looks at a small subset of the highest priority jobs and builds a schedule using only those. The "backfill scheduler" looks at all the pending jobs ordered by priority and QOS and tries to schedule those jobs as efficiently as possible.
In order to keep the system as full as possible, the backfill scheduler must be able to get all the way through its list of pending jobs in a timely manner. Each iteration through the list of jobs is called a "scheduling cycle". If the queue backlog is very long, slurm may not be able to make it through a complete scheduling cycle and the system would fall back to the loosely packed schedule made by the immediate scheduler. This can cause very large inefficiencies in utilization. To avoid this, the backfill scheduler only looks at the first 100 jobs per association (a combination of user, cluster, partition, and account). Of those jobs, it will only schedule jobs above a certain priority (when a job is scheduled squeue --start will show an estimated start time). It will only schedule lower priority jobs in this list if they can start immediately (i.e. there's enough free nodes to run the job) and they won't delay already scheduled jobs.
squeue --start
As a toy example we can think of a case where Slurm has built a schedule of higher priority jobs. The next scheduled high priority job is a 10 node job. Currently 5 nodes are free and 5 more nodes will free up in an hour. The backfill scheduler will put two lower priorty jobs on those idle nodes: one that needs 1 node for 15 minutes and one that needs 4 nodes for 59 minutes. It will continue to do this until there's no jobs that can finish before the original 10 node job can start.
The scheduling algorithm rebuilds itself from scratch each time. If a higher priority job is submitted, it can interject itself and reorder the whole schedule. This is the main reason it's very hard to predict the start times of jobs.