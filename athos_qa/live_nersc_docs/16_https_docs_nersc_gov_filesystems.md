# Source: https://docs.nersc.gov/filesystems/

## File Systems overview ¶


## Storage Systems Usage and Characteristics ¶


## Summary ¶

File systems at NERSC are optimized for different purposes. Our compute systems have access to at least three different file systems with different levels of performance, data persistence, and available capacity. In addition to these basic attributes, the file systems differ in whether and how backups are made, whether files are purged on occasion, and whether they organize data by individual user or by project, as listed in the table below.
Warning
NERSC storage systems are architected to cover different needs for performance, capacity, and data persistance, not as disaster-proof data storage. We have some very limited backup capabilities , but we do not keep multiple copies of data. Do not store the only copy of your data at NERSC: make sure you have at least one copy at another institution or cloud service

## Usage Limits ¶

Each file system has its own limits for space and number of inodes (files or directories) per user or project. We call these quotas. See Filesystem Quotas and Purging for detailed information about inode, space quotas, and file system purge policies.
Files in the Community (CFS) and Common file systems are charged to the project, while files on the Home and Scratch file systems are charged to the file owner; your files in another user's directory will still be charged to your quota. If shared access is needed on the Home or Scratch file system, consider using a Collaboration account .
Directories on the Common and Community file systems are designed to be used by all members of a project and have the setgid bit set by default, which makes all directories and files inherit the group ID and allows other members of the same group to read and write to those files. Some groups may prefer to disable this behavior, which can be done by removing the setgid bit on the desired directory.
If desired, multiple top-level directories can be created on CFS for a project. Each top-level CFS directory comes with its own quota (drawn out of the total quota allocated for the entire project) and could be set to have different group ownership. For instance, if a project m9999 at NERSC wanted to have separate directories for their alpha and beta groups, they could request two directories (e.g. m9999_alpha and m9999_beta ). The quotas for each top-level directory can be allocated in iris by the project's PI . Additionally, if the PI wanted to limit access to these directories to only subsets of their users, they could also adjust the owning groups (e.g. m9999_alpha is owned by group alpha etc.). The PI for m9999 could then add users in their projects to the appropriate groups to allow them access to each directory as desired.
m9999
alpha
beta
m9999_alpha
m9999_beta
m9999_alpha
alpha

## NERSC Global File Systems (NGF) ¶

NERSC Global File Systems (NGF) is a collection of centerwide file systems that are mounted on multiple systems at NERSC, always at a location whose path begins with /global. There are three main file systems that comprise NGF: one providing home directories (global homes), one providing a common login user environment for all our systems (global common), and one for sharing data among collaborators on a science project or team (Community). The main focus of NGF is data sharing, ease of workflow management, and data analysis.
Permanent, relatively small storage for files such as source code or shell scripts. This file system is not tuned for high performance on parallel jobs: use the more optimized Common file system to store applications that need to be sourced by more than a dozen nodes at a time, or applications composed of several packages and small files such as conda environments. Referenced by the environment variable $HOME .
$HOME
A performant platform to install software stacks and compile code. Mounted read-only on Perlmutter compute nodes.
Large, permanent, medium-performance file system. Community directories are intended for sharing data within a group of researchers and for storing data that will be accessed in the medium term (i.e., 1 - 2 years). The PI toolbox can help PIs and PI Proxies fix permissions in their Community project directories.

## Scratch File System ¶

Perlmutter has a dedicated, large, local, parallel scratch file system based on Lustre. The scratch file system is intended for temporary uses such as storage of checkpoints or application input and output during jobs. To facilitate data staging, Perlmutter's scratch file system is also mounted on the DTNs . We have more details on Perlmutter's scratch on the respective page.

## Archive (HPSS) ¶

A high-capacity tape archive intended for long-term storage of inactive and important data, accessible from all systems at NERSC. Space quotas are allocation dependent.
The High Performance Storage System (HPSS) is a modern, flexible, performance-oriented mass storage system. It has been used at NERSC for archival storage since 1998. HPSS is intended for long-term storage of data that is not frequently accessed.

## Local storage ¶

The following file systems provide high I/O performance but often don't preserve data across different jobs, so they are meant to be used as scratch space, and data produced must be staged out at the end of the computation.
Access is always per-user, since these file systems are only accessible within a single SLURM job (XFS and in-RAM file systems), and SLURM purges the content afterwards.
Shifter users can access a fast, per-node xfs file system to improve I/O.
Compute nodes have a small amount of temporary local storage that can be used to improve I/O.

## Backups ¶

See Backups for details about where, how, and when files are backed up at NERSC. Be sure you keep offsite copies of any crucial data.