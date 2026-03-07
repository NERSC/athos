# Source: https://docs.nersc.gov/filesystems/archive/

## The HPSS Archive System ¶


## Usage ¶

The High Performance Storage System (HPSS) is a modern, flexible, performance-oriented mass storage system. HPSS is intended for long-term storage of data that is not frequently accessed.
Storing data in such a system requires a little more effort than storing on a local disk or a typical mounted file system. Files should be stored in appropriately sized chunks. In particular, storing many small files in HPSS is very inefficient, whereas extremely large files can be unwieldy, so users should aim for sizes between 100 GB and 2 TB. The HPSS command-line tools hsi and htar allow you to move files in and out and address the need for grouping. The commands tar and split can be helpful for breaking up large files.
hsi
htar
tar
split
Warning
Storing a large number of smaller files without bundling them is likely to cause performance issues in the system and may cause NERSC to temporarily disable the user's access to HPSS without prior notice. For a discussion of why, see the best practices page.
Retrieving files requires a little thought as well. If you're retreiving many files, you should order the retrievals so that the system can pull the data efficiently. NERSC provides scripts for retrieving files in order . Taking a little time to learn how to use these HPSS utilities will save you headaches.
By default, every user has an HPSS account. Usage charges are based on settings in Iris. See HPSS Usage Charging and Data Sharing for details.

## Quotas ¶

Projects receive HPSS allocations at the same time that computational resources are allocated. DOE's Office of Science awards an HPSS quota to each NERSC project every year. See HPSS Usage Charging and Data Sharing for details.

## Backup ¶

By default, a single copy of the data will be written to tape. Data loss due to hardware faults can occur, but is very rare. Critical data should be manually protected by making an explicit second copy: you can make another copy within the data archive, but for better data protection copy the data to another location.

## A Beginner's Guide to HPSS ¶

This section contains a few quick instructions to get you started using HPSS. We recommend you also review the best practices and read about HPSS usage charging and data sharing . For more in-depth information about HPSS commands, see the pages about hsi and htar .
hsi
htar
You can access NERSC's HPSS in a variety of different ways. hsi and htar are command line tools that offer the best ways to transfer data in and out of HPSS within NERSC. hsi is used to put individual files or directories into HPSS. htar is used to put bundles of files into HPSS, similar to how the tar utility works.
hsi
htar
hsi
htar
tar

## Storing and Fetching Files with hsi ¶

hsi
You can log onto HPSS by using hsi
hsi
nersc$ hsi
nersc$ hsi
Typing just hsi alone transfers you to an HPSS command shell, which looks very similar to a regular login environment. It has a directory structure you can navigate through, and most regular linux commands will work (like ls , cd , etc.). However, commands like ls will only show files and directories stored in the HPSS archive, and only hsi commands will work. It's effectively like sshing to another system called hpss . To exit from the HPSS command shell, use exit .
hsi
ls
cd
ls
hsi
hpss
exit
One can execute hsi commands from any Perlmutter login node or a Data Transfer Node by either typing hsi <command> or hsi alone first, then the commands once you enter the HPSS command shell.
hsi
hsi <command>
hsi
Here's a list of some common hsi commands. The commands below are written assuming you are running from a login node (i.e., you haven't first invoked an HPSS command shell):
hsi
Show the content of your HPSS home directory: hsi ls
hsi ls
Create a remote directory in your home: hsi mkdir new_dir_123
hsi mkdir new_dir_123
Store a single file into HPSS without renaming: hsi put my_local_file
hsi put my_local_file
Store a directory tree, creating sub-dirs when needed: hsi put -R my_local_dir
hsi put -R my_local_dir
Fetch a single file from HPSS into the local directory without renaming: hsi get /path/to/my_hpss_file
hsi get /path/to/my_hpss_file
Delete a file from HPSS: hsi rm /path/to/my_hpss_file
hsi rm /path/to/my_hpss_file
To recursively remove a directory and all of its contained sub-directories and files: hsi rm -R /path/to/my_hpss_dir/
hsi rm -R /path/to/my_hpss_dir/
Delete an empty directory: hsi rmdir /path/to/my_hpss_dir/
hsi rmdir /path/to/my_hpss_dir/
The example below finds files that are more than 20 days old and redirects the output to the file temp.txt :
temp.txt
hsi -q "find . -ctime 20" > temp.txt 2>&1
hsi -q "find . -ctime 20" > temp.txt 2>&1
For more details on using hsi refer to the hsi page.
hsi

## Storing groups of files in HPSS with htar ¶

htar
It's generally recommended that you group your files together into bundles whenever possible. htar is an HPSS application that will create a bundle of files and store it directly in HPSS. The next example shows how to create a bundle with the contents of the directory nova and the file simulator :
htar
nova
simulator
nersc$ htar -cvf nova.tar nova simulator
nersc$ htar -cvf nova.tar nova simulator
Listing the contents of a tar file:
nersc$ htar -tf nova.tar
nersc$ htar -tf nova.tar
To extract a specific file simulator from an htar file nova.tar
simulator
htar
nova.tar
nersc$ htar -xvf nova.tar simulator
nersc$ htar -xvf nova.tar simulator
For more details on using htar , refer to the htar page.
htar

## Token Generation ¶

The first time you try to connect from a NERSC system (Perlmutter, DTNs, etc.) using a NERSC provided client like hsi or htar , you will be prompted for your NERSC password + one-time password, which will generate a token stored in $HOME/.netrc. After completing this step, you will be able to connect to HPSS without typing a password.
hsi
htar
nersc$ hsi Generating .netrc entry... Password + OTP:
nersc$ hsi Generating .netrc entry... Password + OTP:
Sometimes the .netrc file can become out of date or otherwise corrupted. This generates errors that look like this:
nersc$ hsi result = -11000, errno = 29 Unable to authenticate user with HPSS. result = -11000, errno = 9 Unable to setup communication to HPSS... *** HSI: error opening logging Error - authentication/initialization failed
nersc$ hsi result = -11000, errno = 29 Unable to authenticate user with HPSS. result = -11000, errno = 9 Unable to setup communication to HPSS... *** HSI: error opening logging Error - authentication/initialization failed
If this error occurs, try moving your $HOME/.netrc file to $HOME/.netrc_temp . Then connect to the HPSS system again and enter your NERSC password + one-time password when prompted. A new $HOME/.netrc file will be generated with a new token. Alternatively, you can generate the token manually. If the problem persists, contact account support.
$HOME/.netrc
$HOME/.netrc_temp
$HOME/.netrc
You can manually generate a token for accessing HPSS by going to Iris and selecting the blue "Storage" tab. Scroll down to the section labeled "HPSS Tokens" and you will see buttons to generate a token from within NERSC. This button will generate a token which you can paste into a file named .netrc in your home directory. (See Iris for users for more about Iris.)
.netrc
machine archive.nersc.gov
login <your NERSC user name>
password <token generated by Iris>
machine archive.nersc.gov
login <your NERSC user name>
password <token generated by Iris>
The .netrc file should only have user readable permissions. If it's group or world readable, HPSS access will fail.
.netrc

## Session Limits ¶

Users are limited to 15 concurrent sessions. This number can be temporarily reduced if a user is impacting system usability for others.

## Transfers Between HPSS and Facilities Outside NERSC ¶

NERSC's HPSS system can be accessed from outside the center by using Globus . For more information about using Globus, please see our Globus page . The NERSC HPSS endpoint is called "NERSC HPSS". You can use the command line or the web interface to transfer HPSS files. Unfortunately, with the web interface, there is no explicit ordering by tape of file retrievals.
Caution
If you're retrieving a large data set from HPSS with Globus, please see our Globus page for instructions on how to best retrieve files in correct tape order using the command line interface for Globus.

## About HPSS Hardware and Software ¶

HPSS is Hierarchical Storage Management (HSM) software developed by a collaboration of DOE labs and IBM. NERSC is a participant in that collaboration. The software has been used at NERSC for archival storage since 1998. Our HPSS system is a tape system that uses HSM software to ingest data onto a high-performance disk cache and automatically migrate it to a very large enterprise tape subsystem for long-term retention. The disk cache in HPSS is designed to retain many days' worth of new data, and the tape subsystem is designed to provide the most cost-effective long-term scalable data storage available.