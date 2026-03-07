# Source: https://docs.nersc.gov/filesystems/global-common/

## Global Common ¶

The Global Common File System is a global file system available on all NERSC computational systems. It offers a performant platform to install software stacks and compile code. Directories are provided by default to every NERSC project. Additional Global Common directories can be provided upon request.
Warning
Global Common is mounted read-only on the compute nodes. If you need to modify or create files in Global Common, please use the login nodes.

## Usage ¶

Global Common directories are created in /global/common/software . The name of a "default" project directory is the same as its associated NERSC project. There is also a Unix group with the same name; all members of the NERSC project are also members of the group. Access to the Global Common directory is controlled by membership in this group. Because this directory is shared across all systems, you may want to install your software stacks into separate subdirectories depending on the system or the processing architecture. For some general programs you can use the same installs across all systems, but for best performance, we recommend separate installs for each system and architecture.
/global/common/software

## Quotas ¶

Your group usage can be viewed with the showquota --cmn PROJECT [PROJECT [..]] command, which will report quotas for all projects you pass as arguments.
showquota --cmn PROJECT [PROJECT [..]]
Note
See quotas for detailed information about inode, space quotas, and file system purge policies.

## Performance ¶

The Global Common File System is mounted on compute nodes via DVS, an I/O forwarder. The file system is optimized for software installation. It has a smaller block size and is mounted read-only on the computes. This allows us to turn on client-side caching which dramatically decreases the read time of shared libraries across many nodes.

## Backup ¶

All NERSC users should backup important files on a regular basis. Ultimately, it is the user's responsibility to prevent data loss.
Warning
No managed backups of Global Common directories are done by NERSC.