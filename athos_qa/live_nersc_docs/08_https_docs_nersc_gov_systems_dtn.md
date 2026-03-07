# Source: https://docs.nersc.gov/systems/dtn/

## Data Transfer Nodes ¶


## Overview ¶

The data transfer nodes are NERSC servers dedicated to performing transfers between NERSC data storage resources such as HPSS, the Community File System, Perlmutter Scratch, and storage resources at other sites. These nodes are being managed (and monitored for performance) as part of a collaborative effort between ESnet and NERSC to enable high performance data movement over the high-bandwidth 100Gb ESnet wide-area network (WAN).

## Configuration ¶

All DTNs have :
Two 100-gigabit links for transfers to the internet
Two 100-gigabit links for NERSC internal access to storage
Similar to other NERSC systems, users will maintain their own shell configuration files ("dot files").

## Access ¶

There are four data transfer nodes available for interactive use (e.g. via ssh) at dtn0[1-4].nersc.gov, and a pool of nodes used for automated transfer services like Globus.
All NERSC users are automatically given access to the data transfer nodes. The nodes support both interactive use via SSH (direct login) or data transfer using GridFTP services; however, we recommend using Globus for large data transfers.

## Available File Systems ¶

The NERSC data transfer nodes provide access to Global Homes, Global Common, the Community File System (CFS), Perlmutter Scratch, and HPSS. On the DTNs Perlmutter Scratch is mounted at /global/pscratch and can be accessed using the $SCRATCH environment variable.
/global/pscratch
$SCRATCH
Tip Please note that /tmp is very small. Although certain common tools (e.g., vi) use /tmp for temporary storage, users should never explicitly use /tmp for data.
Please note that /tmp is very small. Although certain common tools (e.g., vi) use /tmp for temporary storage, users should never explicitly use /tmp for data.

## File Transfer Software ¶

For most cases, we recommend Globus because it provides the best transfer rates. It makes transfers trivial so users do not have to learn command line options for manual performance tuning. Globus also does automatic performance tuning and has been shown to perform comparable to -- or even better (in some cases) than -- expert-tuned GridFTP. Users can also use GridFTP to transfer large files by hand.
For smaller files you can use Secure Copy ( scp ) or Secure FTP ( sftp ) or rsync to transfer files between two hosts.
scp
sftp
rsync

## Restrictions ¶

In order to keep the data transfer nodes performing optimally for data transfers, we request that users restrict interactive use of these systems to tasks that are related to preparing data for transfer or are directly related to data transfer of some form or fashion. Examples of intended usage would be running python scripts to download data from a remote source, running client software to load data from a file system into a remote database, or compressing (gzip) or bundling (tar) files in preparation for data transfer. Examples of what should not be done include running a database on the server to do data processing, or running tests that saturate the nodes resources. The goal is to maintain data transfer systems that have adequate memory and CPU available for interactive user data transfers.
If you need a space for a more complex workflow, NERSC has a workflow QOS .