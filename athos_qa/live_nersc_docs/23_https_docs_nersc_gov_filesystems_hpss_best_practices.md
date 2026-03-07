# Source: https://docs.nersc.gov/filesystems/HPSS-best-practices/

## HPSS Best Practices ¶

The best guide for how files should be stored in HPSS is how you might want to retrieve them. If you are backing up against accidental directory deletion or failure, then you would want to store your files in a structure where you use htar to separately bundle up each directory. On the other hand, if you are archiving data files, you might want to bundle things up according to the month the data was taken or detector run characteristics, etc. The optimal size for htar bundles is between 100 GB and 2 TB, so you may need to do several htar bundles for each set depending on the size of the data. Other best practices described in this section include
htar
htar
htar
Grouping smaller files
Ordering large retrievals
Avoiding very large files
Clearing disk cache after backing up
Using Globus to access data remotely
Using the xfer QOS for long-running transfers

## Group Small Files Together ¶

If you need to store many files smaller than 100 GB, please use htar to bundle them together before archiving. HPSS is a tape system and responds differently than a typical file system. If you upload large numbers of small files, they will be spread across dozens or hundreds of tapes, requiring multiple loads into tape drives and repositionings of the tape. Storing many small files in HPSS without bundling them together will result in extremely long retrieval times for these files and will slow down the HPSS system for all users.
htar

## Order Large Retrievals ¶

If you are retrieving many (> 100) files from HPSS, you need to order your retrievals so that all files on a single tape will be retrieved in a single pass in the order they are on the tape. This is most easily accomplished by creating a list of the files you want ordered by their appearance on tape and using that with the hsi or htar command. NERSC has several scripts to help you generate an ordered list for retrievals with these commands.
hsi
htar
When retrieving large amounts of compressed data all at once where the total size of the tape archived data is >100 TB and each data chunk is >100 GB, it is advised to raise a ticket and reach out to the HPSS team in order to receive detailed guidance in performing the retrieval incrementally. It helps ensure that all our users have access to HPSS simultaneously.
Caution
If you're retrieving a large data set from HPSS with Globus, please see our Globus page for instructions on how to best retrieve files in correct tape order using the command line interface for Globus.

## Generating A Tape-Sorted List ¶

The script generate_sorted_list_for_hpss.py (already available in your shell path) will generate a list of tape-sorted files. This list can be used for htar or hsi to extract the files. For hsi , please see the description below for a more advanced script that will also re-create the directory structure you had in HPSS.
generate_sorted_list_for_hpss.py
htar
hsi
hsi
To use the script, you first need a list of fully qualified file path names. If you do not already have such a list, you can query HPSS using the following command:
hsi -q 'ls -1 -R <HPSS_files_you_want_to_retrieve>' |& egrep -v '/$|\.idx$' > temp.txt
hsi -q 'ls -1 -R <HPSS_files_you_want_to_retrieve>' |& egrep -v '/$|\.idx$' > temp.txt
(the stdout+stderr pipe to grep removes directories and index files from the output, keeping only files). Once you have the list of files, feed it to the sorting script:
generate_sorted_list_for_hpss.py -i temp.txt |grep -v "Generating sorted list from input file" > sorted_list.txt
generate_sorted_list_for_hpss.py -i temp.txt |grep -v "Generating sorted list from input file" > sorted_list.txt
The file sorted_list.txt will have a sorted list of files to retrieve. If these are htar files, you can extract them with htar into your current directory:
sorted_list.txt
htar
htar
nersc$ awk '{print "htar -xvf",$1}' sorted_list.txt > extract.script nersc$ chmod u+x extract.script nersc$ ./extract.script
nersc$ awk '{print "htar -xvf",$1}' sorted_list.txt > extract.script nersc$ chmod u+x extract.script nersc$ ./extract.script
Tip
You can use the xfer QOS to parallelize your extractions using the sorted list. Just split the list into N smaller lists and and submit N separate xfer jobs.

## Ordering hsi Retrievals and Recreating Directory Structure ¶

hsi
The script hpss_get_sorted_files.py (already available in your shell path) will retrieve the files in the proper tape order and also recreate the directory structure the files had in HPSS.
hpss_get_sorted_files.py
To use the script, you first need a list of fully qualified file path names and/or directory path names. If you do not already have such a list, you can query HPSS using the following command:
hsi -q 'ls -1 -R <HPSS_files_or_directories_you_want_to_retrieve>' |& grep -v '/$' > temp.txt
hsi -q 'ls -1 -R <HPSS_files_or_directories_you_want_to_retrieve>' |& grep -v '/$' > temp.txt
(the stdout+stderr pipe to grep removes directories from the output, keeping only files). Once you have the list of files, feed it to the sorting script:
hpss_get_sorted_files.py -i temp.txt -o <your_target_directory, 
default is current directory> -s <strip string, default is NONE>
hpss_get_sorted_files.py -i temp.txt -o <your_target_directory, 
default is current directory> -s <strip string, default is NONE>
For files in HPSS under /home/e/elvis/unique_data, you might want to strip off /home/e/elvis from the target directory. You can do that by adding the -s /home/e/elvis flag.
/home/e/elvis
-s /home/e/elvis

## Avoid Very Large Files ¶

Files sizes greater than 2 TB can be difficult for HPSS to work with and lead to longer transfer times, increasing the possibility of transfer interruptions. Generally it's best to aim for file sizes in the 100 GB to 2 TB range. NERSC reserves the right to terminate HPSS transfers for files 20 TB or larger because these tie up resources on the system and are rarely successfully retrieved.
You can use tar and split to break up large aggregates or large files into 500 GB sized chunks:
tar
split
tar cvf - myfiles* | split -d --bytes=500G - my_output_tarname.tar.
tar cvf - myfiles* | split -d --bytes=500G - my_output_tarname.tar.
This will generate a number of files with names like my_output_tarname.tar.00 , my_output_tarname.tar.01 , which you can use hsi put to archive into HPSS. When you retrieve these files, you can recombine them with cat:
my_output_tarname.tar.00
my_output_tarname.tar.01
hsi put
cat my_output_tarname.tar.* | tar xvf -
cat my_output_tarname.tar.* | tar xvf -
Tip
If you're generating these chunks on the Lustre file system, be sure to follow the Lustre striping guidelines .

## Clear Disk Cache After Backing Up ¶

When working with a large amount of data, it is a good practice to delete the data from the disk cache as soon as it has been backed up on HPSS. This helps ensure optimal usage of HPSS resources. If individual files larger than 1GB are stored, and they are not going to be used in the near future, users are encouraged to reach out and ask for these files to be purged from disk cache. Additionally, users may themselves clear the cache by running the hsi command migrate -f -P <filepath> . The -P will enforce that the disk copy is removed, once the tape copy has been created. Note that the migrate command will hang until migration to tape is completed. To avoid this delay, users may want to wait till the file has been automatically sent to tape by HPSS before running the migrate command. To check if data has been saved at tape level, use ls -V <filepath> . Alternatively, as files should be migrated automatically by HPSS in the hours after they are stored in HPSS, issuing the migrate -P command 12 or 24 hours after the file was created could be an easier way to achieve a similar result.
migrate -f -P <filepath>
-P
ls -V <filepath>
migrate -P

## Use Globus to Access HPSS Data Remotely ¶

Users can access HPSS data remotely by using Globus . We recommend a two-stage process to move data to or from HPSS and a remote site. Use Globus to transfer the data between NERSC and the remote site (your scratch or CFS directory would make a useful temporary staging point at NERSC), and use hsi or htar to move the data into or out of HPSS.
hsi
htar

## Use the Xfer QOS ¶

Use the dedicated xfer QOS for long-running transfers to or from HPSS. You can also submit jobs to the xfer QOS after your computations are done. The xfer QOS is configured to limit the number of running jobs per user to the same number as the limit of HPSS sessions.