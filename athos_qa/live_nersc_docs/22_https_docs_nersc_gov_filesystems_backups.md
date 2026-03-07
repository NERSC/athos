# Source: https://docs.nersc.gov/filesystems/backups/

## Backups ¶

Danger
All NERSC users should back up important files to HPSS on a regular basis. You should also have at least one copy of critical data stored outside of NERSC. Ultimately, it is your responsibility to protect yourself from data loss.

## Snapshots ¶

Global Homes, Global Common and Community use a snapshot capability to provide users a seven-day history of their directories. A snapshot refers to a technology that creates a point-in-time copy of data, essentially capturing the current state of a system at a specific moment, allowing users to quickly revert back to that state if needed. Running cd .snapshots in either your $HOME directory, your project directory under /global/common/software or your project directory under global/cfs/cdirs will take you to the snapshots of that directory. From there ls will show a directory for each snapshot, named for the date of the snapshot. You can navigate to the snapshot and directory of interest, and copy files from the snapshot to a new location.
cd .snapshots
$HOME
/global/common/software
global/cfs/cdirs
ls
In summary:
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
Warning
These snapshots make it possible to recover accidentally-deleted data, but are not architected to provide disaster protection - we do not have multiple or off-site copies of data. For this reason you should ensure you have other copies, in other locations, of all critical data.

## Purging ¶

Note
See Filesystem Quotas and Purging for detailed information about inode, space quotas, and file system purge policies.
Warning
$SCRATCH directories are not backed up
$SCRATCH