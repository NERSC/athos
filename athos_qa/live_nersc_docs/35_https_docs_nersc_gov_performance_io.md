# Source: https://docs.nersc.gov/performance/io/

## I/O Resources at NERSC ¶

NERSC provides a range of online resources to assist users developing, deploying, understanding, and tuning their scientific I/O workloads, supplemented by direct support from the NERSC Consultants. Here, we provide a consolidated summary of these resources, along with pointers to relevant online documentation.

## Libraries and Tools available at NERSC ¶

NERSC provides a number of I/O middleware libraries, as well as tools for profiling I/O performed by your jobs and monitoring system status. These resources include:
High-level I/O libraries available at NERSC, including the popular HDF5 and NetCDF libraries
The Darshan job-level I/O profiling tool may be used to examine the I/O activity of your own jobs.
Users should keep in mind the entire HPC I/O stack in order to design the best I/O strategy for the long term.
Please refer to the resources below which present more detailed introductions to some of these topics in tutorial form.

## Best Practices for Scientific I/O ¶

While there is clearly a wide range of I/O workloads associated with the many scientific applications deployed at NERSC, there are a number of general guidelines for achieving good performance when accessing our file systems from parallel codes. Some of the most important guidelines include:
Use file systems for their intended use-case; for example, don't use your home directory for production I/O (more details on intended use case may be found on the NERSC file systems page ).
Know what fraction of your wall-clock time is spent in I/O; for example, with estimates provided by Darshan , profiling of critical I/O routines (such as with Craypat 's trace groups), or explicit timing / instrumentation.
When algorithmically possible: Avoid workflows that produce large numbers of small files (e.g. a "file-per-process" access model at high levels of concurrency). Avoid random-access I/O workloads in favor of contiguous access. Prefer I/O workloads that perform large transfers that are similar in size or larger than, and are also aligned with, the underlying file system storage granularity (e.g. blocksize on GPFS-based file systems, stripe width on Lustre-based file systems). If using Fortran list-directed I/O, consider using runtime environment variables to increase the read buffer size (e.g. FORT_FMT_RECL for the Intel Fortran runtime). Use high-level libraries for data management and parallel I/O operations (as these will often apply optimizations in line with the above suggestions, such as MPI-IO collective buffering to improve aggregate transfer size, alignment, and contiguous access).
Avoid workflows that produce large numbers of small files (e.g. a "file-per-process" access model at high levels of concurrency).
Avoid random-access I/O workloads in favor of contiguous access.
Prefer I/O workloads that perform large transfers that are similar in size or larger than, and are also aligned with, the underlying file system storage granularity (e.g. blocksize on GPFS-based file systems, stripe width on Lustre-based file systems). If using Fortran list-directed I/O, consider using runtime environment variables to increase the read buffer size (e.g. FORT_FMT_RECL for the Intel Fortran runtime).
FORT_FMT_RECL
Use high-level libraries for data management and parallel I/O operations (as these will often apply optimizations in line with the above suggestions, such as MPI-IO collective buffering to improve aggregate transfer size, alignment, and contiguous access).
With these suggestions in mind, there are also file system-specific tuning parameters which may be used to enable high-performance I/O on Lustre. Details can be found on the Lustre file system tuning page for Perlmutter $SCRATCH
$SCRATCH

## Tutorials, Support, and Resource Allocation ¶

Here, we list additional support resources for NERSC users, as well as pointers to previous and ongoing research projects associated with NERSC staff and LBL researchers to support high-performance scientific I/O.

## Online tutorials at NERSC ¶

A brief overview of I/O Formats at in use NERSC (focused on MPI I/O and HDF5)

## User support at NERSC ¶

Consulting services provided by NERSC Consultants