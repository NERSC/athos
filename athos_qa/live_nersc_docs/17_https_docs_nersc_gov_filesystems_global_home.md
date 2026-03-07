# Source: https://docs.nersc.gov/filesystems/global-home/

## Global HOME ¶

Home directories provide a convenient means for a user to have access to files such as dotfiles, source files, and configuration files regardless of the platform.

## Usage ¶

Home directories at NERSC should be readable and writable by only their owning user. If you wish to share data with another NERSC member, please see our Data Sharing pages for appropriate methods.
Refer to your home directory using the environment variable $HOME whenever possible. The absolute path may change, but the value of $HOME will always be correct.
$HOME
$HOME

## Quotas ¶

Warning
Quota increases in Global Homes are approved only in extremely unusual circumstances.
Note
See quotas for detailed information about inode, space quotas, and file system purge policies.

## Performance ¶

The Global Homes File System is mounted on compute nodes via DVS, an I/O forwarder. The file system is optimized for small files and is suitable for compiling and linking executables. Global home directories are not intended for large, streaming I/O. Large scale user jobs should not be run in your $HOME directory (this covers a single big jobs or lots of many single node jobs running concurrently). Please see our DVS page for more instructions on where to best install your software.
$HOME

## Backups ¶

All NERSC users should backup important files on a regular basis. Ultimately, it is the user's responsibility to prevent data loss. However, NERSC provides some mechanisms in protecting against data loss.

## Snapshots ¶

A snapshot capability is used to provide users a seven-day history of their home directories. Every directory and sub-directory in $HOME contains a .snapshots entry.
$HOME
.snapshots
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