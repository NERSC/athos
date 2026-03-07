# Source: https://docs.nersc.gov/filesystems/community/

## Community File System (CFS) ¶

The Community File System (CFS) is a global file system available on all NERSC computational systems. It allows sharing of data between users, systems, and the "outside world".
We strongly advise storing a copy of your important data at multiple sites for disaster recovery: please consult the NERSC data policy .

## Usage ¶

Every NERSC project has an associated Community directory and Unix group. Community directories are created in /global/cfs/cdirs . All members of the project have access through their membership in the unix group. There is an environment variable $CFS (which expands to /global/cfs/cdirs/ ) that can be used to access your CFS directory:
/global/cfs/cdirs
$CFS
/global/cfs/cdirs/
nersc$ cd $CFS/<your_project_name>
nersc$ cd $CFS/<your_project_name>

## Multiple Directories Per Project ¶

Occasionally there are cases where the single directory per project model is too limiting. For example, large projects with multiple working groups may wish to have separate Community directories with separate quotas for each working group. In these cases, a PI or PI Proxy for a project may request an additional Community directory (up to a limit of 10) with a specific name via the Iris Storage tab . If you need more than 10 directories, please open a ticket.
Because of the way quotas are managed, these directories can only be "top" level directories. For instance, you can create /global/cfs/cdirs/new_directory_name with a separately managed quota, but not /global/cfs/cdirs/existing_directory_name/new_directory_name . If you wish to present your users with a single directory path to work with, you can create links to these other directories inside your main directory:
/global/cfs/cdirs/new_directory_name
/global/cfs/cdirs/existing_directory_name/new_directory_name
nersc$ ls -l /global/cfs/cdirs/existing_directory_name
drwxrws---  3 elvis nstaff   4.0K Feb 18 21:19 random_directory
lrwxrwxrwx  1 elvis nstaff      7 Feb 18 21:20 new_directory_name -> /global/cfs/cdirs/new_directory_name
nersc$ ls -l /global/cfs/cdirs/existing_directory_name
drwxrws---  3 elvis nstaff   4.0K Feb 18 21:19 random_directory
lrwxrwxrwx  1 elvis nstaff      7 Feb 18 21:20 new_directory_name -> /global/cfs/cdirs/new_directory_name
Projects Can Split Quotas Between Directories
A project is awarded a single total value for their Community storage allocation as part of the ERCAP process. This storage allocation can be split between their Community directories on the Iris Storage tab .

## Permission Adjustments ¶

PIs and PI Proxies can use the PI Toolbox to adjust permissions in their CFS directories: they can change the group or owner of files and directories, change group-level permissions, or make all files and directories within their project directory group readable.

## Quotas ¶

Quotas on the Community File System are determined by NERSC based on information PIs supply in their yearly ERCAP requests. If you need a mid-year quota increase on the Community File System, please use the Disk Quota Increase Form and we will pass the information along to the appropriate group for approval.
More Quota Details
See quotas for detailed information about inode, space quotas, and file system purge policies.

## Performance ¶

The Community File System is mounted on compute nodes via DVS , an I/O forwarder. The file system has a peak aggregate bandwidth of at least 100 GB/sec for streaming I/O. While user applications that depend on high-bandwidth for streaming large files can use the Community File System, it is recommended to use the local scratch file system instead.
Use the Read Only DVS Mount of CFS for Better Performance
If many of the processes in your jobs repeatedly read in the same file (e.g. a configuration file), you may see a large speedup by using a read-only DVS mount. Please see our DVS page for more information.

## Backup ¶

All NERSC users should backup important files on a regular basis. Ultimately, it is the user's responsibility to prevent data loss. However, NERSC provides some mechanisms in protecting against data loss.

## Snapshots ¶

Community directories use a snapshot capability to provide users a seven-day history of their contents. Every directory and sub-directory in a Community directory contains a ".snapshots" entry.
.snapshots is invisible to ls , ls -a , find and similar commands
.snapshots
ls
ls -a
find
Contents are visible through ls -F .snapshots
ls -F .snapshots
Can be browsed normally after cd .snapshots
cd .snapshots
Files cannot be created, deleted or edited in snapshots
Files can only be copied out of a snapshot

## Lifetime ¶

Community directories will remain in existence as long as the owning project is active. Projects typically "end" at the end of a NERSC Allocation Year. This happens when the PI chooses not to renew the project, or DOE chooses not to provide an allocation for a renewal request. In either case, the following steps will occur following the termination of the project:
-365 days - The start of the new Allocation Year and no Project renewal The data in the Community directory will remain available on the Community File System until the start of the next Allocation Year.
-365 days - The start of the new Allocation Year and no Project renewal
The data in the Community directory will remain available on the Community File System until the start of the next Allocation Year.
+0 days - The start of the following Allocation Year PIs notified that the affected Community directory will be archived, and then removed from the file system in 90 days.
+0 days - The start of the following Allocation Year
PIs notified that the affected Community directory will be archived, and then removed from the file system in 90 days.
+30 days The Community directory will become read-only.
+30 days
The Community directory will become read-only.
+60 days The full pathname to the Community directory will be modified. Automated scripts will likely fail.
+60 days
The full pathname to the Community directory will be modified. Automated scripts will likely fail.
+90 days User access to the directory will be terminated and directories may be removed from the file system.
+90 days
User access to the directory will be terminated and directories may be removed from the file system.