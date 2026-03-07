# Source: https://docs.nersc.gov/jobs/examples/

## Example job scripts ¶

For details of terminology used on this page please see our jobs overview . Correct affinity settings are essential for good performance.
The examples on this page focus on Perlmutter CPU architectures.
For Perlmutter GPU , please see the running jobs on Perlmutter page.

## Basic MPI batch script ¶

One MPI process per physical core.
#!/bin/bash #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=2 #SBATCH --ntasks-per-node=128 #SBATCH --constraint=cpu srun check-mpi.gnu.pm
#!/bin/bash #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=2 #SBATCH --ntasks-per-node=128 #SBATCH --constraint=cpu srun check-mpi.gnu.pm

## Hybrid MPI+OpenMP jobs ¶

Warning
In Slurm each hyper thread is considered a "cpu" so the --cpus-per-task option must be adjusted accordingly. Generally best performance is obtained with 1 OpenMP thread per physical core. Additional details about affinity settings .
--cpus-per-task

## Example 1 ¶

One MPI process per socket and 1 OpenMP thread per physical core
#!/bin/bash #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=2 #SBATCH --ntasks-per-node=2 #SBATCH --cpus-per-task=128 #SBATCH --constraint=cpu export OMP_PROC_BIND = spread export OMP_PLACES = threads export OMP_NUM_THREADS = 64 srun check-hybrid.gnu.pm
#!/bin/bash #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=2 #SBATCH --ntasks-per-node=2 #SBATCH --cpus-per-task=128 #SBATCH --constraint=cpu export OMP_PROC_BIND = spread export OMP_PLACES = threads export OMP_NUM_THREADS = 64 srun check-hybrid.gnu.pm

## Example 2 ¶

28 MPI processes with 32 OpenMP threads per process, each OpenMP thread has 1 physical core
Note
The addition of --cpu-bind=cores is useful for getting correct affinity settings .
--cpu-bind=cores
#!/bin/bash #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=7 #SBATCH --ntasks=28 #SBATCH --cpus-per-task=64 #SBATCH --constraint=cpu export OMP_PROC_BIND = spread export OMP_PLACES = threads export OMP_NUM_THREADS = 32 srun --cpu-bind = cores check-hybrid.gnu.pm
#!/bin/bash #SBATCH --qos=debug #SBATCH --time=5 #SBATCH --nodes=7 #SBATCH --ntasks=28 #SBATCH --cpus-per-task=64 #SBATCH --constraint=cpu export OMP_PROC_BIND = spread export OMP_PLACES = threads export OMP_NUM_THREADS = 32 srun --cpu-bind = cores check-hybrid.gnu.pm

## Interactive ¶

Interactive jobs are launched with the salloc command.
salloc
Tip
On Perlmutter, the interactive QOS has a higher priority than other QOSes.
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint gpu --gpus 4 --account=mxxxx
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint gpu --gpus 4 --account=mxxxx
Note
Please see the interactive section for more details of interactive QOS on NERSC systems.

## Multiple Parallel Jobs Sequentially ¶

Multiple sruns can be executed one after another in a single batch script. Be sure to specify the total walltime needed to run all jobs.
In the following example, each srun uses 4 nodes to run, and the 4 sruns are run one after another.
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=4 #SBATCH --time=10:00 #SBATCH --licenses=cfs,scratch #SBATCH --constraint=cpu srun -n 128 -c 8 --cpu_bind = cores ./a.out srun -n 64 -c 16 --cpu_bind = cores ./b.out srun -n 32 -c 32 --cpu_bind = cores ./c.out
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=4 #SBATCH --time=10:00 #SBATCH --licenses=cfs,scratch #SBATCH --constraint=cpu srun -n 128 -c 8 --cpu_bind = cores ./a.out srun -n 64 -c 16 --cpu_bind = cores ./b.out srun -n 32 -c 32 --cpu_bind = cores ./c.out
Tip
Workflow tools are another option to help you run multiple parallel sequential jobs.

## Multiple Parallel Jobs Simultaneously ¶

Multiple sruns can be executed simultaneously in a single batch script.
Tip
Be sure to specify the total number of nodes needed to run all jobs at the same time.
Note
By default, multiple concurrent srun executions cannot share compute nodes under Slurm in the non-shared QOSs.
Don't run too many sruns
Running too many sruns in the same job or multiple sruns in a loop can cause contention in the scheduler, effecting your tasks as well as other users tasks running on the system. For running many small tasks in parallel we recommend looking into the workflow tools we support at NERSC. for i = 1 = 10 ,000 srun -n 1 a.out
for i = 1 = 10 ,000 srun -n 1 a.out
for i = 1 = 10 ,000 srun -n 1 a.out
In the following example, a total of 176+432+160 = 786 cores are required, which would hypothetically fit on 768/128 = 6 Perlmutter CPU nodes. However, because sruns cannot share nodes by default, we instead have to dedicate:
2 nodes to the first execution (176 cores)
4 to the second (432 cores)
2 to the third (160 cores)
For all three executables the node is not fully packed and number of MPI tasks per node is not a divisor of 256, so both -c and --cpu-bind flags are used in srun commands.
-c
--cpu-bind
srun
Note
The " & " at the end of each srun command and the wait command at the end of the script are very important to ensure the jobs are run in parallel and the batch job will not exit before all the simultaneous sruns are completed.
&
srun
wait
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=8 #SBATCH --time=30:00 #SBATCH --licenses=scratch #SBATCH --constraint=cpu srun -N 2 -n 176 -c 2 --cpu_bind = cores ./a.out & srun -N 4 -n 432 -c 2 --cpu_bind = cores ./b.out & srun -N 2 -n 160 -c 2 --cpu_bind = cores ./c.out & wait
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=8 #SBATCH --time=30:00 #SBATCH --licenses=scratch #SBATCH --constraint=cpu srun -N 2 -n 176 -c 2 --cpu_bind = cores ./a.out & srun -N 4 -n 432 -c 2 --cpu_bind = cores ./b.out & srun -N 2 -n 160 -c 2 --cpu_bind = cores ./c.out & wait

## Running jobs with GPU power caps ¶

The default GPU power limit on Perlmutter is 400 W. Lowering it may significantly reduce energy use with minimal performance impact. The script below shows how to set a 200 W power cap for GPUs. For details, see the GPU Power Capping documentation.
#!/bin/bash #SBATCH -J pc200 #SBATCH -q regular #SBATCH -C gpu #SBATCH -N 2 #SBATCH -G 8 #SBATCH -t 4:00:00 #SBATCH -A mxyz #SBATCH --gpu-power=200 #SBATCH -o %x-%j.out #Other settings go here srun -n 8 -c 32 --cpu-bind = cores -G 8 --gpu-bind = none ./a.out
#!/bin/bash #SBATCH -J pc200 #SBATCH -q regular #SBATCH -C gpu #SBATCH -N 2 #SBATCH -G 8 #SBATCH -t 4:00:00 #SBATCH -A mxyz #SBATCH --gpu-power=200 #SBATCH -o %x-%j.out #Other settings go here srun -n 8 -c 32 --cpu-bind = cores -G 8 --gpu-bind = none ./a.out

## Command line submission of common jobs ¶

If you want to run a simple command on a compute node, you can use the srun command which can be useful to run a quick job without having to create a batch script. Shown below are some example jobs you can run with srun .
srun
srun
srun --constraint = cpu --ntasks = 1 --time 5 --qos debug hostname
srun --constraint = cpu --ntasks = 1 --time 5 --qos debug hostname
srun --constraint = gpu --ntasks = 1 -G 1 --time 5 -A <account> --qos debug nvidia-smi
srun --constraint = gpu --ntasks = 1 -G 1 --time 5 -A <account> --qos debug nvidia-smi
--wrap
The --wrap option can be used to wrap an arbitrary command on a compute node. This can be useful when you want to submit a job without having to create a job script.
--wrap
In example below we will run the nvidia-smi command on a GPU node.
nvidia-smi
elvis@perlmutter> sbatch --constraint = gpu --ntasks = 1 -G 1 --time 5 -A <account> --qos debug --wrap = "nvidia-smi" Submitted batch job 273892
elvis@perlmutter> sbatch --constraint = gpu --ntasks = 1 -G 1 --time 5 -A <account> --qos debug --wrap = "nvidia-smi" Submitted batch job 273892
xfer
The xfer QOS can be used to transfer files between compute systems and HPSS. Shown below is an example of running hostname in the xfer QOS.
xfer
hostname
xfer
elvis@perlmutter> srun --qos xfer --time 12 :00:00 hostname
srun: job 273895 queued and waiting for resources
srun: job 273895 has been allocated resources
login01
elvis@perlmutter> srun --qos xfer --time 12 :00:00 hostname
srun: job 273895 queued and waiting for resources
srun: job 273895 has been allocated resources
login01

## Job Arrays ¶

Job arrays offer a mechanism for submitting and managing collections of similar jobs quickly and easily.
This example submits 3 jobs. Each job uses 1 node and has the same time limit and QOS. The SLURM_ARRAY_TASK_ID environment variable is set to the array index value.
SLURM_ARRAY_TASK_ID
Perlmutter CPU
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=1 #SBATCH --constraint=cpu #SBATCH --time=2 #SBATCH --array=0-2 echo $SLURM_ARRAY_TASK_ID
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=1 #SBATCH --constraint=cpu #SBATCH --time=2 #SBATCH --array=0-2 echo $SLURM_ARRAY_TASK_ID
Additional examples and details
Slurm job array documentation
Manual pages via man sbatch on NERSC systems
man sbatch
Tip
In many use cases, GNU Parallel is a superior solution to task arrays. This is because the Slurm scheduler prioritizes fewer jobs requesting many nodes ahead of many jobs requesting fewer nodes (array tasks are considered individual jobs). Other workflow tools are available as well.

## Dependencies ¶

Job dependencies can be used to construct complex pipelines or chain together long simulations requiring multiple steps.
Note
The --parsable option to sbatch can simplify working with job dependencies.
--parsable
sbatch
Example
jobid = $( sbatch --parsable first_job.sh ) sbatch --dependency = afterok: $jobid second_job.sh
jobid = $( sbatch --parsable first_job.sh ) sbatch --dependency = afterok: $jobid second_job.sh
Example
jobid1 = $( sbatch --parsable first_job.sh ) jobid2 = $( sbatch --parsable --dependency = afterok: $jobid1 second_job.sh ) jobid3 = $( sbatch --parsable --dependency = afterok: $jobid1 third_job.sh ) sbatch --dependency = afterok: $jobid2 ,afterok: $jobid3 last_job.sh
jobid1 = $( sbatch --parsable first_job.sh ) jobid2 = $( sbatch --parsable --dependency = afterok: $jobid1 second_job.sh ) jobid3 = $( sbatch --parsable --dependency = afterok: $jobid1 third_job.sh ) sbatch --dependency = afterok: $jobid2 ,afterok: $jobid3 last_job.sh
Note
A job that is dependent on another job does not accumulate eligible queue wait time before the dependency is satisfied.
Tip
Workflow tools are another option to help you manage job dependencies.

## Shared ¶

In the shared QOS, unlike other QOSes, a single node can be shared by multiple users or jobs. Jobs in the shared QOS are charged for each physical core in allocated to the job.
Tip
In many use cases, GNU Parallel is a superior solution to using a shared QOS. This is because the Slurm scheduler prioritizes fewer jobs requesting many nodes ahead of many jobs requesting fewer nodes.
The number of physical cores allocated to a job by Slurm is controlled by three parameters:
-n ( --ntasks )
-n
--ntasks
-c ( --cpus-per-task )
-c
--cpus-per-task
--mem - Total memory available to the job ( MemoryRequested )
--mem
MemoryRequested
Note
In Slurm a "cpu" corresponds to a hyperthread . So there are 2 cpus per physical core .
The memory on a node is divided evenly among the "cpus" (or hyperthreads):
The number of physical cores used by a job is computed by
Perlmutter CPU MPI
A two rank MPI job which utilizes 2 physical cores (and 4 hyperthreads) of a Perlmutter CPU node.
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=2 #SBATCH --cpus-per-task=2 srun --cpu-bind = cores ./a.out
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=2 #SBATCH --cpus-per-task=2 srun --cpu-bind = cores ./a.out
A two rank MPI job which utilizes 4 physical cores (and 8 hyperthreads) of a Perlmutter CPU node.
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=2 #SBATCH --cpus-per-task=4 export OMP_NUM_THREADS = 2 srun --cpu-bind = cores ./a.out
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=2 #SBATCH --cpus-per-task=4 export OMP_NUM_THREADS = 2 srun --cpu-bind = cores ./a.out
An OpenMP only code which utilizes 6 physical cores.
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=1 #SBATCH --cpus-per-task=12 export OMP_NUM_THREADS = 6 ./my_openmp_code.exe
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=1 #SBATCH --cpus-per-task=12 export OMP_NUM_THREADS = 6 ./my_openmp_code.exe
A serial job should start by requesting a single slot and increase the amount of memory required only as needed to maximize throughput and minimize charge and wait time.
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=1 #SBATCH --mem=1GB ./serial.exe
#!/bin/bash #SBATCH --qos=shared #SBATCH --constraint=cpu #SBATCH --time=5 #SBATCH --nodes=1 #SBATCH --ntasks=1 #SBATCH --mem=1GB ./serial.exe

## Open MPI ¶

On Perlmutter, applications built with Open MPI can be launched via srun or Open MPI's mpirun command. The module openmpi needs to be loaded to build an application against Open MPI. Typically one builds the application using the mpicc (for C Codes), mpifort (for Fortran codes), or mpiCC (for C++ codes) commands. Alternatively, Open MPI supports use of pkg-config to obtain the include and library paths. For example, pkg-config --cflags --libs ompi-c returns the flags that must be passed to the backend c compiler (e.g. gcc, gfortran, icc, ifort) to build against Open MPI. Open MPI also supports Java MPI bindings. Use mpijavac to compile Java codes that use the Java MPI bindings. For Java MPI, it is highly recommended to launch jobs using Open MPI's mpirun command. Note the Open MPI packages at NERSC do not support static linking.
openmpi
mpicc
mpifort
mpiCC
pkg-config
pkg-config --cflags --libs ompi-c
c
mpijavac
See Open MPI for more information about using Open MPI on NERSC systems.
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=2 #SBATCH --ntasks-per-node=32 #SBATCH --constraint=cpu #SBATCH -AmXXXX (<----- put in your project number here) # # cray-mpich and cray-libsci conflict with openmpi so will automatically be unloaded. # module load openmpi

/bin/cat <<EOM > ring_c.c /* * Copyright (c) 2004-2006 The Trustees of Indiana University and Indiana *                         University Research and Technology *                         Corporation.  All rights reserved. * Copyright (c) 2006      Cisco Systems, Inc.  All rights reserved. * * Simple ring test program in C. */ #include <stdio.h> #include "mpi.h" int main(int argc, char *argv[]) { int rank, size, next, prev, message, tag = 201; /* Start up MPI */ MPI_Init(&argc, &argv); MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size); /* Calculate the rank of the next process in the ring.  Use the modulus operator so that the last process "wraps around" to rank zero. */ next = (rank + 1) % size; prev = (rank + size - 1) % size; /* If we are the "master" process (i.e., MPI_COMM_WORLD rank 0), put the number of times to go around the ring in the message. */ if (0 == rank) { message = 10; printf("Process 0 sending %d to %d, tag %d (%d processes in ring)\n", message, next, tag, size); MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); printf("Process 0 sent to %d\n", next); } /* Pass the message around the ring.  The exit mechanism works as follows: the message (a positive integer) is passed around the ring.  Each time it passes rank 0, it is decremented.  When each processes receives a message containing a 0 value, it passes the message on to the next process and then quits.  By passing the 0 message first, every process gets the 0 message and can quit normally. */ while (1) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); if (0 == rank) { --message; printf("Process 0 decremented value: %d\n", message); } MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); if (0 == message) { printf("Process %d exiting\n", rank); break; } } /* The last process does one extra send to process 0, which needs to be received before the program can exit */ if (0 == rank) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); } /* All done */ MPI_Finalize(); return 0; } EOM mpicc -o ring_c ring_c.c
mpirun -np 64 ring_c # # run again with srun # srun --mpi = pmix -n 64 ring_c
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=2 #SBATCH --ntasks-per-node=32 #SBATCH --constraint=cpu #SBATCH -AmXXXX (<----- put in your project number here) # # cray-mpich and cray-libsci conflict with openmpi so will automatically be unloaded. # module load openmpi

/bin/cat <<EOM > ring_c.c /* * Copyright (c) 2004-2006 The Trustees of Indiana University and Indiana *                         University Research and Technology *                         Corporation.  All rights reserved. * Copyright (c) 2006      Cisco Systems, Inc.  All rights reserved. * * Simple ring test program in C. */ #include <stdio.h> #include "mpi.h" int main(int argc, char *argv[]) { int rank, size, next, prev, message, tag = 201; /* Start up MPI */ MPI_Init(&argc, &argv); MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size); /* Calculate the rank of the next process in the ring.  Use the modulus operator so that the last process "wraps around" to rank zero. */ next = (rank + 1) % size; prev = (rank + size - 1) % size; /* If we are the "master" process (i.e., MPI_COMM_WORLD rank 0), put the number of times to go around the ring in the message. */ if (0 == rank) { message = 10; printf("Process 0 sending %d to %d, tag %d (%d processes in ring)\n", message, next, tag, size); MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); printf("Process 0 sent to %d\n", next); } /* Pass the message around the ring.  The exit mechanism works as follows: the message (a positive integer) is passed around the ring.  Each time it passes rank 0, it is decremented.  When each processes receives a message containing a 0 value, it passes the message on to the next process and then quits.  By passing the 0 message first, every process gets the 0 message and can quit normally. */ while (1) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); if (0 == rank) { --message; printf("Process 0 decremented value: %d\n", message); } MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); if (0 == message) { printf("Process %d exiting\n", rank); break; } } /* The last process does one extra send to process 0, which needs to be received before the program can exit */ if (0 == rank) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); } /* All done */ MPI_Finalize(); return 0; } EOM mpicc -o ring_c ring_c.c
mpirun -np 64 ring_c # # run again with srun # srun --mpi = pmix -n 64 ring_c
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=2 #SBATCH --ntasks-per-node=32 #SBATCH --constraint=gpu #SBATCH --gpus-per-node=4 #SBATCH -AmXXXX (<----- put in your project number here) # # cray-mpich and cray-libsci conflict with openmpi so will automatically be unloaded. # module load openmpi

/bin/cat <<EOM > ring_c.c /* * Copyright (c) 2004-2006 The Trustees of Indiana University and Indiana *                         University Research and Technology *                         Corporation.  All rights reserved. * Copyright (c) 2006      Cisco Systems, Inc.  All rights reserved. * * Simple ring test program in C. */ #include <stdio.h> #include "mpi.h" int main(int argc, char *argv[]) { int rank, size, next, prev, message, tag = 201; /* Start up MPI */ MPI_Init(&argc, &argv); MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size); /* Calculate the rank of the next process in the ring.  Use the modulus operator so that the last process "wraps around" to rank zero. */ next = (rank + 1) % size; prev = (rank + size - 1) % size; /* If we are the "master" process (i.e., MPI_COMM_WORLD rank 0), put the number of times to go around the ring in the message. */ if (0 == rank) { message = 10; printf("Process 0 sending %d to %d, tag %d (%d processes in ring)\n", message, next, tag, size); MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); printf("Process 0 sent to %d\n", next); } /* Pass the message around the ring.  The exit mechanism works as follows: the message (a positive integer) is passed around the ring.  Each time it passes rank 0, it is decremented.  When each processes receives a message containing a 0 value, it passes the message on to the next process and then quits.  By passing the 0 message first, every process gets the 0 message and can quit normally. */ while (1) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); if (0 == rank) { --message; printf("Process 0 decremented value: %d\n", message); } MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); if (0 == message) { printf("Process %d exiting\n", rank); break; } } /* The last process does one extra send to process 0, which needs to be received before the program can exit */ if (0 == rank) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); } /* All done */ MPI_Finalize(); return 0; } EOM mpicc -o ring_c ring_c.c
mpirun -np 64 ring_c # # run again with srun # srun --mpi = pmix -n 64 ring_c
#!/bin/bash #SBATCH --qos=debug #SBATCH --nodes=2 #SBATCH --ntasks-per-node=32 #SBATCH --constraint=gpu #SBATCH --gpus-per-node=4 #SBATCH -AmXXXX (<----- put in your project number here) # # cray-mpich and cray-libsci conflict with openmpi so will automatically be unloaded. # module load openmpi

/bin/cat <<EOM > ring_c.c /* * Copyright (c) 2004-2006 The Trustees of Indiana University and Indiana *                         University Research and Technology *                         Corporation.  All rights reserved. * Copyright (c) 2006      Cisco Systems, Inc.  All rights reserved. * * Simple ring test program in C. */ #include <stdio.h> #include "mpi.h" int main(int argc, char *argv[]) { int rank, size, next, prev, message, tag = 201; /* Start up MPI */ MPI_Init(&argc, &argv); MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size); /* Calculate the rank of the next process in the ring.  Use the modulus operator so that the last process "wraps around" to rank zero. */ next = (rank + 1) % size; prev = (rank + size - 1) % size; /* If we are the "master" process (i.e., MPI_COMM_WORLD rank 0), put the number of times to go around the ring in the message. */ if (0 == rank) { message = 10; printf("Process 0 sending %d to %d, tag %d (%d processes in ring)\n", message, next, tag, size); MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); printf("Process 0 sent to %d\n", next); } /* Pass the message around the ring.  The exit mechanism works as follows: the message (a positive integer) is passed around the ring.  Each time it passes rank 0, it is decremented.  When each processes receives a message containing a 0 value, it passes the message on to the next process and then quits.  By passing the 0 message first, every process gets the 0 message and can quit normally. */ while (1) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); if (0 == rank) { --message; printf("Process 0 decremented value: %d\n", message); } MPI_Send(&message, 1, MPI_INT, next, tag, MPI_COMM_WORLD); if (0 == message) { printf("Process %d exiting\n", rank); break; } } /* The last process does one extra send to process 0, which needs to be received before the program can exit */ if (0 == rank) { MPI_Recv(&message, 1, MPI_INT, prev, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE); } /* All done */ MPI_Finalize(); return 0; } EOM mpicc -o ring_c ring_c.c
mpirun -np 64 ring_c # # run again with srun # srun --mpi = pmix -n 64 ring_c

## Xfer QOS ¶

The intended use of the xfer QOS is to transfer data between compute systems and HPSS. xfer jobs run on one of the system login nodes and are free of charge. If you want to transfer data to the HPSS archive system at the end of a regular job, you can submit an xfer job at the end of your batch job script. On Perlmutter, this can be done with sbatch -q xfer -C cron hsi put <my_files> and xfer jobs can be monitored via squeue . The number of running jobs for each user is limited to the number of concurrent HPSS sessions (15).
xfer
xfer
xfer
sbatch -q xfer -C cron hsi put <my_files>
xfer
squeue
Warning
Do not run computational jobs in the xfer QOS.
xfer
#!/bin/bash #SBATCH --qos=xfer #SBATCH -C cron #SBATCH --time=12:00:00 #SBATCH --job-name=my_transfer #SBATCH --licenses=SCRATCH #Archive run01 to HPSS htar -cvf run01.tar run01
#!/bin/bash #SBATCH --qos=xfer #SBATCH -C cron #SBATCH --time=12:00:00 #SBATCH --job-name=my_transfer #SBATCH --licenses=SCRATCH #Archive run01 to HPSS htar -cvf run01.tar run01
xfer jobs specifying -N nodes will be rejected at submission time. By default, xfer jobs get 2GB of memory allocated. The memory footprint scales somewhat with the size of the file, so if you're archiving larger files, you'll need to request more memory. You can do this by adding #SBATCH --mem=XGB to the above script (where X in the range of 5 - 10 GB is a good starting point for large files).
xfer
-N nodes
xfer
#SBATCH --mem=XGB

## Preemptible Jobs ¶

If your application suffers few consequences when inturrupted, such as being composed of many short tasks in a workflow or having the ability to checkpoint and restore, then it may benefit by using a preempt QOS. These preemptible QOS can potentially offer faster queue throughput by separating a single long job into multiple shorter sections which backfill faster, and are discounted relative to other QOS. See QOS limits and charges for the current preemption time and charge factor.
preempt
Note the following details if your application wishes to be warned in advance when being preempted:
The amount of advance notice given by Slurm is between 60 and 120 seconds. This amount is configured for the entire system and no user options are available to modify it.
A SIGTERM signal is sent only to processes launched by an srun command. There is no way for job preemption to warn the batch script or a process launched outside of srun . The kind of signal sent cannot be changed.
srun
srun
The sbatch --signal flag has no influence over the behavior of job preemption.
--signal
The --requeue flag only acts automatically in the case of preemption; it does not requeue a job that reaches timeout. If you wish to requeue in both situations you will need a second handler for the timeout signal that includes the manual requeue command: scontrol requeue ${SLURM_JOB_ID}
--requeue
scontrol requeue ${SLURM_JOB_ID}
Add a "sleep 120" command to the end of scripts which expect to be preempted. If no processes are running before the final SIGKILL is sent then Slurm will record a job state other than PREEMPTED.
Perlmutter CPU preemptable driver and payload scripts
#!/bin/bash #SBATCH -q preempt #SBATCH -C cpu #SBATCH -N 1 #SBATCH --time=24:00:00 #SBATCH --signal=USR1@60 #SBATCH --requeue #SBATCH --open-mode=append srun variable-time-payload.sh
sleep 120 # make sure a process is still running for slurm to send SIGKILL to #!/bin/bash preempt_handler () { #place here: commands to run when preempt signal (SIGTERM) arrives from slurm kill -TERM ${ 1 } #forward SIGTERM signal to the user application #if --requeue was used, slurm will automatically do so here } timeout_handler () { #place here: commands to run when timeout signal (set outside to USR1) arrives kill -TERM ${ 1 } #forward SIGTERM signal to the user application #manually requeue here because slurm *will not* do it automatically scontrol requeue ${ SLURM_JOB_ID } } # sleep 10000 & #user application replaces here, must be backgrounded pid = $! trap "preempt_handler ' $pid '" SIGTERM #this catches preempt SIGTERM from slurm trap "timeout_handler ' $pid '" USR1 #this catches timeout USR1 from slurm wait sleep 120 #keep the job step alive until slurm sends SIGKILL
#!/bin/bash #SBATCH -q preempt #SBATCH -C cpu #SBATCH -N 1 #SBATCH --time=24:00:00 #SBATCH --signal=USR1@60 #SBATCH --requeue #SBATCH --open-mode=append srun variable-time-payload.sh
sleep 120 # make sure a process is still running for slurm to send SIGKILL to
#!/bin/bash #SBATCH -q preempt #SBATCH -C cpu #SBATCH -N 1 #SBATCH --time=24:00:00 #SBATCH --signal=USR1@60 #SBATCH --requeue #SBATCH --open-mode=append srun variable-time-payload.sh
sleep 120 # make sure a process is still running for slurm to send SIGKILL to
#!/bin/bash preempt_handler () { #place here: commands to run when preempt signal (SIGTERM) arrives from slurm kill -TERM ${ 1 } #forward SIGTERM signal to the user application #if --requeue was used, slurm will automatically do so here } timeout_handler () { #place here: commands to run when timeout signal (set outside to USR1) arrives kill -TERM ${ 1 } #forward SIGTERM signal to the user application #manually requeue here because slurm *will not* do it automatically scontrol requeue ${ SLURM_JOB_ID } } # sleep 10000 & #user application replaces here, must be backgrounded pid = $! trap "preempt_handler ' $pid '" SIGTERM #this catches preempt SIGTERM from slurm trap "timeout_handler ' $pid '" USR1 #this catches timeout USR1 from slurm wait sleep 120 #keep the job step alive until slurm sends SIGKILL
#!/bin/bash preempt_handler () { #place here: commands to run when preempt signal (SIGTERM) arrives from slurm kill -TERM ${ 1 } #forward SIGTERM signal to the user application #if --requeue was used, slurm will automatically do so here } timeout_handler () { #place here: commands to run when timeout signal (set outside to USR1) arrives kill -TERM ${ 1 } #forward SIGTERM signal to the user application #manually requeue here because slurm *will not* do it automatically scontrol requeue ${ SLURM_JOB_ID } } # sleep 10000 & #user application replaces here, must be backgrounded pid = $! trap "preempt_handler ' $pid '" SIGTERM #this catches preempt SIGTERM from slurm trap "timeout_handler ' $pid '" USR1 #this catches timeout USR1 from slurm wait sleep 120 #keep the job step alive until slurm sends SIGKILL
When using sacct to check on a job with requeued components, adding the --duplicates flag (or just -D ) instructs Slurm to display information about all requeued portions of the same job instead of just one.
sacct
--duplicates
-D
A debug_preempt QOS is available to help test and validate job preemption behaviors. It has a much shorter minimum time before preemption is possible. These are the fastest steps to intentionally cause a job preemption:
debug_preempt
Submit job to debug_preempt QOS.
debug_preempt
Check the queue to know when the job has started and run for at least 5 minutes.
Use sqs -j jobid to find the name of a node the job is running on. ( nidXXXXXX )
sqs -j jobid
nidXXXXXX
Submit a job to the interactive QOS with the flag -w nidXXXXXX . This requests a specific node and will drive the preemption of your first job.
-w nidXXXXXX
The DMTCP tool is a natural combination with job preemption and automated requeueing.

## MPMD (Multiple Program Multiple Data) Jobs ¶

Slurm supports running a job with different programs and different arguments for each task. MPMD jobs are useful for certain applications, such as when multiple executables sharing a single MPI_COMM_WORLD, yet each executable has the need to use different task configurations on compute nodes.
One mechanism to run MPMD jobs is via mutiple set of srun flags separated by a : . Here is a sample batch job script:
:
Example
Uses 3 Perlmutter CPU nodes #!/bin/bash #SBATCH --qos=regular #SBATCH --constraint=cpu #SBATCH --nodes=3 #SBATCH --time=01:00:00 srun -N 1 -n 64 -c 4 --cpu-bind = cores ./a.out : -N 2 -n 32 -c 16 --cpu-bind = cores ./b.out
#!/bin/bash #SBATCH --qos=regular #SBATCH --constraint=cpu #SBATCH --nodes=3 #SBATCH --time=01:00:00 srun -N 1 -n 64 -c 4 --cpu-bind = cores ./a.out : -N 2 -n 32 -c 16 --cpu-bind = cores ./b.out
#!/bin/bash #SBATCH --qos=regular #SBATCH --constraint=cpu #SBATCH --nodes=3 #SBATCH --time=01:00:00 srun -N 1 -n 64 -c 4 --cpu-bind = cores ./a.out : -N 2 -n 32 -c 16 --cpu-bind = cores ./b.out
where ./a.out runs on 1 node with 64 MPI tasks, and ./b.out runs on 2 nodes using 16 MPI tasks per node. Notice the above command contains only one srun at the beginning of the command line. It is perfectly fine to run the same executable instead of 3 different executables in the above example. Keep in mind each exectuable runs on exclusive compute nodes, i.e., they can not share nodes.
./a.out
./b.out
srun
This is different from Multiple Parallel Jobs While Sharing Nodes examples below where each executable has its own MPI_COMM_WORLD and the executables can share compute nodes.
MPI_COMM_WORLD
Another mechanism to run MPMD jobs is to use --multi-prog <config_file_name> .
--multi-prog <config_file_name>
srun --multi-prog myrun.conf
srun --multi-prog myrun.conf
Again, keep in mind that same exectuable can be used, and the executables can not share compute nodes.

## Configuration file format ¶

Task rank One or more task ranks to use this configuration. Multiple values may be comma separated. Ranges may be indicated with two numbers separated with a - with the smaller number first (e.g. 0-4 and not 4-0 ). To indicate all tasks not otherwise specified, specify a rank of * as the last line of the file. If an attempt is made to initiate a task for which no executable program is defined, the following error message will be produced: No executable program specified for this task .
Task rank
One or more task ranks to use this configuration. Multiple values may be comma separated. Ranges may be indicated with two numbers separated with a - with the smaller number first (e.g. 0-4 and not 4-0 ). To indicate all tasks not otherwise specified, specify a rank of * as the last line of the file. If an attempt is made to initiate a task for which no executable program is defined, the following error message will be produced: No executable program specified for this task .
-
0-4
4-0
*
No executable program specified for this task
Executable The name of the program to execute. May be fully qualified pathname if desired.
Executable
The name of the program to execute. May be fully qualified pathname if desired.
Arguments Program arguments. The expression %t will be replaced with the task's number. The expression %o will be replaced with the task's offset within this range (e.g. a configured task rank value of 1-5 would have offset values of 0-4 ). Single quotes may be used to avoid having the enclosed values interpreted. This field is optional. Any arguments for the program entered on the command line will be added to the arguments specified in the configuration file.
Arguments
Program arguments. The expression %t will be replaced with the task's number. The expression %o will be replaced with the task's offset within this range (e.g. a configured task rank value of 1-5 would have offset values of 0-4 ). Single quotes may be used to avoid having the enclosed values interpreted. This field is optional. Any arguments for the program entered on the command line will be added to the arguments specified in the configuration file.
%t
%o
1-5
0-4

## Example ¶

Sample job script for MPMD jobs. You need to create a configuration file with format described above, and a batch script which passes this configuration file via --multi-prog flag in the srun command.
--multi-prog
Perlmutter CPU
nersc$ cat mpmd.conf 0 -95 ./a.out 96 -255 ./b.out 256 -419 ./c.out

nersc$ cat batch_script.sh #!/bin/bash #SBATCH -q regular #SBATCH -N 5 #SBATCH -n 420  # total of 420 tasks #SBATCH -t 02:00:00 #SBATCH -C cpu srun --multi-prog ./mpmd.conf
nersc$ cat mpmd.conf 0 -95 ./a.out 96 -255 ./b.out 256 -419 ./c.out

nersc$ cat batch_script.sh #!/bin/bash #SBATCH -q regular #SBATCH -N 5 #SBATCH -n 420  # total of 420 tasks #SBATCH -t 02:00:00 #SBATCH -C cpu srun --multi-prog ./mpmd.conf

## Realtime ¶

The "realtime" QOS is used for running jobs with the need of getting realtime turnaround time. This is only intended for jobs that are connected with an external realtime component (e.g. live beamline runs, telescope time, etc.).
Note
Use of this QOS requires special approval, and is only intended for use with a live, external realtime component that needs on-demand resources. There are limited resources available for this QOS. It is not intended to provide faster batch turnaround for regular jobs.
"realtime" QOS Request Form
The realtime QOS is a user-selective shared QOS, meaning you can request either exclusive node access (with the --qos=realtime option) or allow multiple applications to share a node (with the --qos=realtime_shared option).
--qos=realtime
--qos=realtime_shared
Tip
It is recommended to allow sharing the nodes so more jobs can be scheduled in the allocated nodes.
Example
Uses two full Perlmutter CPU nodes #!/bin/bash #SBATCH --qos=realtime #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH --ntasks-per-node=128 #SBATCH --cpus-per-task=2 #SBATCH --time=01:00:00 #SBATCH --job-name=my_job #SBATCH --licenses=cfs #SBATCH --exclusive srun --cpu-bind = cores ./mycode.exe # pure MPI, 256 MPI tasks
#!/bin/bash #SBATCH --qos=realtime #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH --ntasks-per-node=128 #SBATCH --cpus-per-task=2 #SBATCH --time=01:00:00 #SBATCH --job-name=my_job #SBATCH --licenses=cfs #SBATCH --exclusive srun --cpu-bind = cores ./mycode.exe # pure MPI, 256 MPI tasks
#!/bin/bash #SBATCH --qos=realtime #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH --ntasks-per-node=128 #SBATCH --cpus-per-task=2 #SBATCH --time=01:00:00 #SBATCH --job-name=my_job #SBATCH --licenses=cfs #SBATCH --exclusive srun --cpu-bind = cores ./mycode.exe # pure MPI, 256 MPI tasks
Similar to using the "shared" QOS, you can request number of slots on the node (total of CPUs, or 256 slots) by specifying the -ntasks and/or --mem . The rules are the same as the shared QOS.
-ntasks
--mem
Example
Two MPI ranks running with 4 OpenMP threads each. The job is using in total 8 physical cores (8 "cpus" or hyperthreads per "task") and 10GB of memory.
#!/bin/bash #SBATCH --qos=realtime_shared #SBATCH --constraint=cpu #SBATCH --ntasks=2 #SBATCH --cpus-per-task=8 #SBATCH --mem=10GB #SBATCH --time=01:00:00 #SBATCH --job-name=my_job2 #SBATCH --licenses=cfs export OMP_NUM_THREADS = 4 srun --cpu-bind = cores ./mycode.exe
#!/bin/bash #SBATCH --qos=realtime_shared #SBATCH --constraint=cpu #SBATCH --ntasks=2 #SBATCH --cpus-per-task=8 #SBATCH --mem=10GB #SBATCH --time=01:00:00 #SBATCH --job-name=my_job2 #SBATCH --licenses=cfs export OMP_NUM_THREADS = 4 srun --cpu-bind = cores ./mycode.exe
Example
OpenMP only code running with 6 threads. Note that srun is not required in this case.
srun
#!/bin/bash #SBATCH --qos=realtime_shared #SBATCH --constraint=cpu #SBATCH --nodes=1 #SBATCH --ntasks=1 #SBATCH --cpus-per-task=12 #SBATCH --mem=16GB #SBATCH --time=01:00:00 #SBATCH --job-name=my_job3 #SBATCH --licenses=cfs,SCRATCH export OMP_NUM_THREADS = 6 ./mycode.exe
#!/bin/bash #SBATCH --qos=realtime_shared #SBATCH --constraint=cpu #SBATCH --nodes=1 #SBATCH --ntasks=1 #SBATCH --cpus-per-task=12 #SBATCH --mem=16GB #SBATCH --time=01:00:00 #SBATCH --job-name=my_job3 #SBATCH --licenses=cfs,SCRATCH export OMP_NUM_THREADS = 6 ./mycode.exe

## Multiple Parallel Jobs While Sharing Nodes ¶

Under certain scenarios, you might want two or more independent applications running simultaneously on each compute node allocated to your job. For example, a pair of applications that interact in a client-server fashion via some IPC mechanism on-node (e.g. shared memory), but must be launched in distinct MPI communicators.
This latter constraint would mean that MPMD mode (see above) is not an appropriate solution, since although MPMD can allow multiple executables to share compute nodes, the executables will also share an MPI_COMM_WORLD at launch.
MPI_COMM_WORLD
Slurm can allow multiple executables launched with concurrent srun calls to share compute nodes as long as the sum of the resources assigned to each application does not exceed the node resources requested for the job. Importantly, you cannot over-allocate the CPU, memory, or "network" resource. While the former two are self-explanatory, the latter refers to limitations imposed on the number of applications per node that can simultaneously use the current Slingshot interconnect configuration, which is limited to 3.
Here is an example of an sbatch script that uses two compute nodes and runs three applications concurrently. The number of tasks per node is controlled with the -n and -N flags. The --overlap flag is needed to allow overlap on the assigned resources with other job steps and control corresponding memory limit per application.
-n
-N
--overlap
Perlmutter CPU
#!/bin/bash #SBATCH -q regular #SBATCH -N 2 #SBATCH -t 1:00:00 #SBATCH -C cpu srun -N 2 -n 16 -c 4 --overlap ./a.out & srun -N 2 -n 32 -c 2 --overlap ./b.out & srun -N 2 -n 10 -c 8 --overlap ./c.out & wait
#!/bin/bash #SBATCH -q regular #SBATCH -N 2 #SBATCH -t 1:00:00 #SBATCH -C cpu srun -N 2 -n 16 -c 4 --overlap ./a.out & srun -N 2 -n 32 -c 2 --overlap ./b.out & srun -N 2 -n 10 -c 8 --overlap ./c.out & wait
In this use case, multiple applications share part of multiple nodes, such as App A runs on nodes 1 and 2, while App B also runs on nodes 1 and 2 (but on different cores) simultaneously. This example needs to use the --overlap flag to allow multiple sruns to share resources on the same nodes with other job steps. While in the previous "running simultaneous parallel jobs" example, such as App A runs on nodes 1 and 2, and App B simultaneously runs on different nodes 3,4,5. It is perfectly fine to run the same executable instead of 3 different executables in the above example.
--overlap
This is different from MPMD (Multiple Program Multiple Data) jobs examples where multiple executables can not share compute nodes and the executables will also share a single MPI_COMM_WORLD .
MPI_COMM_WORLD
Note
It is permitted to specify srun --network=no_vni which will not count against the Slingshot network resource. This is useful when, for example, launching a bash script or other application that does not use the interconnect. We don't currently anticipate this being a common use case, but if your application(s) do employ this mode of operation it would be appreciated if you let us know.
srun --network=no_vni
Tip
Workflow tools are another option to help you run multiple parallel jobs while sharing nodes.

## Heterogeneous Jobs ¶

Slurm is able to submit and manage a single job which contains several components consisting of different job options. The individual components of a heterogeneous job can select almost all of the slurm job options. Heterogeneous jobs can be useful if parts of a job have different requirements. For example, part of a job might require 4 GPUs whilst the other part of the job requires 256 CPU cores. Likewise, parts of a job may have different memory per cpu requirements and therefore benefit from deploying a heterogeneous job.
Example
A sample heterogeneous perlmutter job: utilising both the CPU and GPU compute nodes.
#!/bin/bash #SBATCH -A <account> #SBATCH --qos=regular #SBATCH --time=05:00:00 #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH hetjob #SBATCH --constraint=gpu #SBATCH --nodes=1 srun --het-group = 0 cpu_script.sh srun -G 4 --het-group = 1 gpu_script.sh
#!/bin/bash #SBATCH -A <account> #SBATCH --qos=regular #SBATCH --time=05:00:00 #SBATCH --constraint=cpu #SBATCH --nodes=2 #SBATCH hetjob #SBATCH --constraint=gpu #SBATCH --nodes=1 srun --het-group = 0 cpu_script.sh srun -G 4 --het-group = 1 gpu_script.sh
Each component of the job should be separated by the #SBATCH hetjob line in the slurm script (as shown above). The --het-group option in srun defines which component(s) are to have applications launched for them. Slurm heterogeneous jobs do support multiple components and each component will appear in squeue .
#SBATCH hetjob
--het-group
srun
squeue
There is also syntax for salloc , sbatch and srun commands. The character : is used to separate each component request. See example below:
salloc
sbatch
srun
:
sbatch --cpus-per-task = 4 --ntasks = 128 : \ --cpus-per-task = 1 --ntasks = 1 my_batch_script.sl
sbatch --cpus-per-task = 4 --ntasks = 128 : \ --cpus-per-task = 1 --ntasks = 1 my_batch_script.sl
For more information on heterogeneous slurm jobs visit their support documentation page .

## Projects That Have Exhausted Their Allocation ¶

A project with zero or negative NERSC-hours balance can submit to the the overrun QOS.
If you meet the overrun criteria , you can access the overrun QOS by submitting with -q overrun ( -q shared_overrun for shared-node jobs). On Perlmutter, all overrun jobs require the --time-min flag at job submission and are subject to preemption by higher priority workloads under certain circumstances.
-q overrun
-q shared_overrun
--time-min
Tip
We recommend you implement checkpoint/restart your overrun jobs to save your progress.
Example
A job requesting a minimum time of 1.5 hours:
sbatch -q overrun --time-min=01:30:00 my_batch_script.sl
sbatch -q overrun --time-min=01:30:00 my_batch_script.sl

## Additional information ¶

sbatch documentation
Manual pages ( man sbatch on NERSC systems)
man sbatch