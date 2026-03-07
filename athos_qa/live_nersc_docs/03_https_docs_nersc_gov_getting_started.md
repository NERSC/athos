# Source: https://docs.nersc.gov/getting-started/

## Getting Started at NERSC ¶

About this page
This document will guide you through the basics of using NERSC's supercomputers, storage systems, and services.
Welcome to the National Energy Research Scientific Computing Center (NERSC)!

## Computing Resources ¶


## Perlmutter ¶

Perlmutter is a HPE Cray EX supercomputer with over 1500 GPU-accelerated compute nodes.
Perlmutter system information
NERSC Center Status

## NERSC Accounts ¶

In order to use the NERSC facilities, you need to obtain a NERSC account and your user account must be tied to a NERSC Allocation . Before logging into any compute resource, you will need to set a strong password. Please see our password rules if you need help creating a strong password. Once you have an account, you can log in to Iris to manage account details. This will include setting up multi-factor authentication (MFA) which is required to access all NERSC systems and services.
MFA is required for NERSC users
Multi-Factor Authentication (MFA)
With Iris you can
Set up multi-factor authentication (MFA)
Check computing allocation balances
Change your password or reset a forgotten password
Create reports about your compute usage at NERSC
Update your contact information
Change your login shell
and more!

## Email ¶

When you get a NERSC user account, an email alias is created for you of the form <username>@nersc.gov that will forward email to your delivery address (set in Iris ).
<username>@nersc.gov
NERSC users email list
As a NERSC user you will be subscribed to the NERSC users email list. Users cannot unsubscribe from this list due to the imporant nature of the information.
NERSC provides several other email lists, including one with additional system status details. You can see more information about these lists at the NERSC email lists webpage .

## Connecting to NERSC ¶

The documentation in this section will guide you through the login process on Perlmutter. Alternatively, feel free to watch the video below.
Quicklinks to help you log in to NERSC resources:
Multi-Factor Authentication (MFA)
SSH
Login nodes
Troubleshooting connection problems
NERSC Center Status

## Storage Resources ¶

File systems at NERSC are configured for different purposes. Perlmutter has access to at least three different file systems with different levels of performance, permanence and available space.
NERSC File System Overview

## Community File System (CFS) ¶

The Community File System (CFS) is a global file system available on all NERSC computational and data transfer systems. It allows sharing of data between users, systems, and the public.
Detailed CFS usage information

## Scratch File System ¶

Perlmutter Scratch is an all-flash Lustre file system designed for high performance temporary storage of large files. It is intended to support intensive I/O for jobs that are being actively computed on the Perlmutter system. We recommend that you run your jobs, especially data intensive ones, from the Perlmutter Scratch File System. The Scratch file system is regularly purged, and files that have been inactive for more than 8 weeks are subject to be purged. It is the responsibility of users to move important data to another permanent storage location after active compute needs have been met.
Detailed Scratch usage information

## High Performance Storage System (HPSS) Archival Storage ¶

The High Performance Storage System (HPSS) is a modern, flexible, performance-oriented mass storage system. It has been used at NERSC for archival storage since 1998. HPSS is intended for long term storage of data that is not frequently accessed.
Detailed HPSS usage information

## Software ¶

NERSC and its vendors supply a rich set of compilers, HPC utilities, programming libraries, development tools, debuggers/profilers, data and visualization tools.
We provide a list of applications that are built by NERSC staff with links to documentation for each. An increasing portion of the NERSC software stack is being provided via the Spack package manager, which helps automate software builds for popular HPC tools.
Software can be accessed via the module command. Currently we support lmod for Perlmutter.
module
Please see our Software Policy outlining our software support model for the NERSC provided software stack.
Something missing?
If there is something missing that you would like to have on our systems, please submit a request and we will evaluate it for appropriateness, cost, effort, and benefit to the community.

## Python ¶

The Python we provide at NERSC is Anaconda Python .
Brief introduction to Python at NERSC
Talk Python at NERSC at New User Training event, September 28, 2022 - Slides , Video

## Machine Learning ¶

NERSC supports a variety of software for machine learning and deep learning on our systems.
Machine Learning at NERSC
Talk Deep Learning at NERSC at New User Training event, September 28, 2022 - Slides , Video

## Computing Environment ¶

Info
$HOME directories are shared across all NERSC systems (except HPSS)
$HOME

## Compiling/ building software ¶

Compilers at NERSC
Shell Environment
Talk Programming Environment and Compilation at New User Training event, September 28, 2022 - Slides , Video

## Running Jobs ¶

Typical usage of the system involves submitting scripts (also referred to as "jobs") to a batch system such as Slurm .
Overview of jobs at NERSC
Rich set of example jobs
!!! Most jobs at NERSC require using the srun command in place of mpirun .
srun
mpirun

## Interactive Computing ¶

NERSC provides interactive computing via interactive slurm jobs and the Jupyter service.

## Debugging and Profiling ¶

NERSC provides many popular debugging and profiling tools.
Performance Tools
Debugging Tools
Talk Debugging Tools at New User Training event, September 28, 2022 - Slides , Video

## Data Sharing ¶


## Security and Data Integrity ¶

Sharing data with other users must be done carefully. Permissions should be set to the minimum necessary to achieve the desired access. For instance, consider carefully whether it's really necessary before sharing write permissions on data. Be sure to have archived backups of any critical shared data. It is also important to ensure that private login secrets (like SSH private keys or apache htaccess files) are not shared with other users (either intentionally or accidentally). Good practice is to keep things like this in a separate directory that is as locked down as possible.

## Transferring Data Within NERSC ¶


## Sharing with Other Members of Your Project ¶

NERSC's Community file system is set up with group read and write permissions and is ideal for sharing with other members of your project. There is a directory for every active project at NERSC and all members of that project should have access to it by default.

## Sharing with NERSC Users Outside of Your Project ¶

You can share files and directories with NERSC users outside of your project by adjusting the unix file permissions. We have an extensive write-up of unix file permissions and how they work.
If you want to share just a few files a single time, you can use NERSC's give/take utilty .
Tip
"Do you need to transfer at all?" If your data is on NERSC Global File Systems ( Community , Common , Home ) transfering data may not be necessary because these file systems are mounted on almost all NERSC systems. However, if you are doing a lot of I/O with these files, you will benefit from staging them on the most performant file system. Usually that's the local Scratch (pscratch) file system, which is only mounted on Perlmutter.
Use the the unix command cp , tar or rsync to copy files within the same computational system. For large amounts of data use Globus to leverage the automatic retry functionality.
cp
tar
rsync

## Sharing Data outside of NERSC ¶

You can easily and quickly share data over the web using our Science Gateways framework.
You can also share large volumes of data externally by setting up a Globus Sharing Endpoint .
Warning
Do not use Magic Wormhole or attempt to install it via pip or from source onto NERSC systems. The NERSC cybersecurity team has reviewed Magic Wormhole and determined that it is a significant security risk and its use violates NERSC's Appropriate Use Policy (AUP). It has therefore been placed on NERSC's list of prohibited software . Instead, we recommend utilizing supported methods such as scp, rsync, or Globus . Please create a ticket at the NERSC help desk if you need help identifying an alternative solution.
Globus is a web-based service that solves many of the challenges encountered moving data between systems. Globus provides the most comprehensive, efficient, and easy to use service for most NERSC users.
However, there are other tools available to transfer data between NERSC and other sites:
scp : standard Linux utilities suitable for smaller files (<1GB)
GridFTP : parallel transfer software for large files

## Data Transfer Nodes ¶

The Data Transfer Nodes (DTNs) are servers dedicated for data transfer based upon the ESnet Science DMZ model. DTNs are tuned to transfer data efficiently, are optimized for bandwidth, and have direct access to most of the NERSC file systems. These transfer nodes are configured within Globus as managed endpoints available to all NERSC users.

## Getting Help ¶

NERSC places a very strong emphasis on enabling science and providing user-oriented systems and services. If you require additional support we encourage you to search our documentation for a solution before opening a ticket.

## Help Desk ¶

Availability
Account support is available 8 a.m. to 5 p.m. Pacific Time on business days.
The online help desk is the preferred method for contacting NERSC.
Before you open a ticket
Password resets can be done automatically without opening a ticket!
We encourage you to search our documentation before opening a ticket.
New users should read this Getting started guide .
Account changes can be processed through Iris ( Iris guide for users ).

## How to File a Good Ticket ¶

NERSC Consultants handle thousands of support requests per year. In order to ensure efficient timely resolution of your issue, include as much of the following as possible when making a request:
error messages
jobids
location of relevant files input/output job scripts source code executables
input/output
job scripts
source code
executables
output of module list
module list
any steps you have tried
steps to reproduce
Please copy and paste any text directly into the ticket and only include screenshots as attachements when the graphical output is the subject of the support request.
Tip
You can make code snippets, shell outputs, etc in your ticket much more readable by inserting a line with:
[code]<pre>
[code]<pre>
before the snippet, and another line with:
</pre>[/code]
</pre>[/code]
after it. While these are the most useful, other options to improve formatting can be found in the full list of formatting options .
Access to the online help system requires logging in with your NERSC username, password, and one-time password. If you are an existing user unable to log in, you can send an email to accounts@nersc.gov for support.
If you are not a NERSC user, you can reach NERSC with your queries at accounts@nersc.gov or allocations@nersc.gov .
accounts@nersc.gov
allocations@nersc.gov

## FAQ ¶

Please see the following links for common issues that can be addressed, if you are still having issues, please create a ticket in help desk .
Password Resets
Connection problems
File Permissions
Troubleshooting Slurm

## Appointments with NERSC User-Support Staff ¶

NERSC provides 30-minute appointments with NERSC expert staff. Before you schedule your appointment consult the list of available topics described below.
Tip
To make the most use of an appointment, we strongly encourage you to try some things on your own and share them with NERSC staff ahead of time using the appointment intake form.
Topics that can be covered during appointments:
NERSC 101: these appointments are for asking basic questions, and you could not find the answer in o ur documentation, or you just don't know where to start.
NERSC 101: these appointments are for asking basic questions, and you could not find the answer in o ur documentation, or you just don't know where to start.
Containers at NERSC: ask for advice on deploying containerized workflows at NERSC using Shifter. We recommend that you download your image to Perlmutter (see [How to Use Shifter] (development/containers/shifter/how-to-use.md)) before the appointment if possible, and be prepared to share your containerfile and the image name.
Containers at NERSC: ask for advice on deploying containerized workflows at NERSC using Shifter. We recommend that you download your image to Perlmutter (see [How to Use Shifter] (development/containers/shifter/how-to-use.md)) before the appointment if possible, and be prepared to share your containerfile and the image name.
NERSC Filesystems: ask for advice on I/O optimization and file systems at NERSC. Possible discussion topics include:
NERSC Filesystems: ask for advice on I/O optimization and file systems at NERSC. Possible discussion topics include:
Optimal file system choices
Optimal file system choices
Quota and file-permission issues
I/O profiling
Refactoring your code
Refactoring your code
GPU Basics: ask for advice on programming GPUs for users that are new to the topic. This category is good for when you have started developing your GPU code, but are encountering problems. These appointment will be the most productive if you have access to source code that runs or can be actively debugged.
GPU Basics: ask for advice on programming GPUs for users that are new to the topic. This category is good for when you have started developing your GPU code, but are encountering problems. These appointment will be the most productive if you have access to source code that runs or can be actively debugged.
Using GPUs in Python: get help with using GPUs through Python, eg. CuPy , RAPIDS , or PyCUDA .
Using GPUs in Python: get help with using GPUs through Python, eg. CuPy , RAPIDS , or PyCUDA .
CuPy
RAPIDS
PyCUDA
Spin: Advice on using Spin at NERSC. All active Spin users are welcome to make an appointment for hands-on help deploying or troubleshooting their apps in Spin. Appointments can currently be scheduled during Spin Office Hours every Friday, 10 a.m. - 12 p.m. Pacific time.
Spin: Advice on using Spin at NERSC. All active Spin users are welcome to make an appointment for hands-on help deploying or troubleshooting their apps in Spin. Appointments can currently be scheduled during Spin Office Hours every Friday, 10 a.m. - 12 p.m. Pacific time.