# Source: https://docs.nersc.gov/filesystems/perlmutter-scratch/

## Perlmutter Scratch ¶

Perlmutter Scratch is an all-flash Lustre file system designed for high performance temporary storage of large files. It is intended to support intensive I/O for jobs that are being actively computed on the Perlmutter system. We recommend that you run your jobs, especially data intensive ones, from the Perlmutter Scratch File System.
Warning
The scratch file system is purged. Any file not accessed within 8 weeks is subject to deletion. Please make sure to back up your important files.

## Usage ¶

The Perlmutter Scratch File system should always be referenced using the environment variable $SCRATCH or $PSCRATCH . On Perlmutter this variable expands to /pscratch/sd/FirstLetterOfUserName/YourUserName . For example, for user, elvis , $PSCRATCH would become /pscratch/sd/e/elvis . Perlmutter scratch is available to all Permutter compute nodes and is tuned for high performance. To facilitate data staging, Perlmutter scratch is also mounted on the DTNs .
$SCRATCH
$PSCRATCH
/pscratch/sd/FirstLetterOfUserName/YourUserName
elvis
$PSCRATCH
/pscratch/sd/e/elvis

## Quotas ¶

If your scratch usage exceeds your quota, you will not be able to write to the file system until you reduce your usage. See Quotas for a listing of quota limits.

## Performance ¶

The Perlmutter Scratch File System is an all-flash file system. It has 44 PB of disk space, an aggregate bandwidth of >6 TB/sec, and 4 million IOPS (4 KiB random). It has 16 MDS (metadata servers) and 370 I/O servers called OSTs.

## Default File Striping ¶

By default files on Perlmutter are striped across a single OST. Given the large number of small files on our system, this is a compromise to ensure reasonable performance for most files. However, some I/O patterns may find better performance with different striping. Please see our Lustre striping page for a longer discussion.

## Backup ¶

All NERSC users should backup important files on a regular basis. Ultimately, it is the user's responsibility to prevent data loss.
Warning
Because the scratch file system is subject to purging, data stored there is always at risk. Please make sure to back up your important files (e.g. to HPSS ).

## File System Purging ¶

File purging is a process where files that are no longer used are automatically removed from the file system. It is an important tool that NERSC uses to clean up unwanted files and improve the performance of the file system. File-system performance decreases as a file system becomes very full, so purging benefits everyone by reducing the load on the file system and ensuring there's enough space for everyone's files.

## Purge Rules and Methods ¶

NERSC uses the access time of a file, also know as atime , to determine which files will be purged. NERSC will not delete files that have been accessed (i.e. read or changed) within 8 weeks without considerable advanced notice.
atime
When Perlmutter Scratch reaches a pre-determined fullness threshold, the purging mechanism is activated and automatically deletes files until the file system usage drops below the threshold. In an effort to avoid unnecessarily removing data and to target older files preferentially over newer files, we may set an access time cutoff that is longer than the 8 week minimum purge threshold. However, users should always assume that any file not accessed within 8 weeks may be purged at any time. All critical data should be backed up to another file system or computing site.

## Purge Candidates ¶

A list of files eligible for purging can be found at $SCRATCH/.purge/candidate_<date>.json . Files on this list met the criteria for purging at the time the list was created. Before a file is purged, the criteria will be rechecked to verify nothing has changed since the candidate list was made. This list is not guaranteed to be a comphensive list of all files that could be purged, so we recommend that you back up all critical data regardless of whether it appears in this list or not.
$SCRATCH/.purge/candidate_<date>.json

## Knowing Which Files Have Been Purged ¶

A historical record of files deleted by the purge process is available at $SCRATCH/.purge/purged_<date>.json . This file preserves the filename and some metadata, including the age of the file at deletion, for each file that was deleted on that date.
$SCRATCH/.purge/purged_<date>.json
The contents of $SCRATCH/.purge/ will not be deleted by our purges to make sure a record of purging activities is retained.
$SCRATCH/.purge/

## Directory Lifetime ¶

Perlmutter scratch directories may be deleted after a user is no longer active.