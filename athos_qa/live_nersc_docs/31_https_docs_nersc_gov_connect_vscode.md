# Source: https://docs.nersc.gov/connect/vscode/

## Visual Studio Code / VSCode ¶

Visual studio code is an advanced IDE (Integrated Development Environment) which has many useful extensions for building and running your code on Perlmutter. There are many useful extensions supported by Microsoft for common HPC tools like Python , C/C++ , as well as many user contributed extensions.

## Connecting with VSCode Remote Window ¶

Connecting to Perlmutter with VSCode Remote - SSH is similar to connecting to any other Linux computer. The most up to date instructions can be found on the Remote SSH extension site. By default VSCode will connect to a Perlmutter login node which can be used for software development but should not be used for computation. For larger computations or to connect to GPUs you should get an allocation on a compute node.
Warning
If your Global HOME usage exceeds your quota, you will not be able to connect to Perlmutter with VSCode. Please make sure to check your quota and move files if necessary.

## Running on a compute node ¶

To connect to a Perlmutter compute node make sure to have a valid ssh key from sshproxy . To configure your ssh client to connect to a compute node you'll need to add the following to your ~/.ssh/config file on the machine you want to connect with. If your NERSC username is different from the username on the computer you are connecting from uncomment and add your NERSC username to each of the configuration blocks.
~/.ssh/config
Host dtn*.nersc.gov perlmutter*.nersc.gov *.nersc.gov LogLevel QUIET IdentityFile ~/.ssh/nersc IdentitiesOnly yes ForwardAgent yes # User nersc_user_name Host nid?????? LogLevel QUIET IdentityFile ~/.ssh/nersc StrictHostKeyChecking no ProxyJump perlmutter.nersc.gov Hostname %h # User nersc_user_name
Host dtn*.nersc.gov perlmutter*.nersc.gov *.nersc.gov LogLevel QUIET IdentityFile ~/.ssh/nersc IdentitiesOnly yes ForwardAgent yes # User nersc_user_name Host nid?????? LogLevel QUIET IdentityFile ~/.ssh/nersc StrictHostKeyChecking no ProxyJump perlmutter.nersc.gov Hostname %h # User nersc_user_name
On Windows systems, OpenSSH keys from sshproxy need to be used with the following C:\Users\myaccount\.ssh\config file:
C:\Users\myaccount\.ssh\config
Host dtn*.nersc.gov perlmutter*.nersc.gov *.nersc.gov LogLevel QUIET IdentityFile C: \U sers \m yaccount \. ssh \n ersc IdentitiesOnly yes ForwardAgent yes # User nersc_user_name Host nid?????? LogLevel QUIET IdentityFile C: \U sers \m yaccount \. ssh \n ersc StrictHostKeyChecking no ProxyJump perlmutter.nersc.gov Hostname %h # User nersc_user_name
Host dtn*.nersc.gov perlmutter*.nersc.gov *.nersc.gov LogLevel QUIET IdentityFile C: \U sers \m yaccount \. ssh \n ersc IdentitiesOnly yes ForwardAgent yes # User nersc_user_name Host nid?????? LogLevel QUIET IdentityFile C: \U sers \m yaccount \. ssh \n ersc StrictHostKeyChecking no ProxyJump perlmutter.nersc.gov Hostname %h # User nersc_user_name
In your VSCode window you'll also need to update two settings, the maxReconnectionAttempts will help to disconnect when the compute node allocation is over and useFlock needs to be set to false as file locking ( flock ) is not supported by the way $HOME directories are mounted on compute nodes.
maxReconnectionAttempts
useFlock
$HOME
"remote.SSH.maxReconnectionAttempts" : 2 "remote.SSH.useFlock" : false
"remote.SSH.maxReconnectionAttempts" : 2 "remote.SSH.useFlock" : false
When connecting you'll first connect to a Perlmutter login node and request and interactive allocation from Slurm with salloc . The following salloc line requests one GPU node for 60 minutes. Remember to change `m0000`` to the account that you want to charge hours from.
salloc
salloc
elvis@laptop[~]$ ssh perlmutter.nersc.gov
elvis@perlmutter-login34[~]$ salloc --nodes 1 --qos interactive --time 
00:60:00 -C gpu -A m0000
salloc: Pending job allocation 19622394
salloc: job 19622394 queued and waiting for resources
salloc: job 19622394 has been allocated resources
salloc: Granted job allocation 19622394
salloc: Waiting for resource configuration
salloc: Nodes nid200021 are ready for job
elvis@perlmutter-nid200021[~]$
elvis@laptop[~]$ ssh perlmutter.nersc.gov
elvis@perlmutter-login34[~]$ salloc --nodes 1 --qos interactive --time 
00:60:00 -C gpu -A m0000
salloc: Pending job allocation 19622394
salloc: job 19622394 queued and waiting for resources
salloc: job 19622394 has been allocated resources
salloc: Granted job allocation 19622394
salloc: Waiting for resource configuration
salloc: Nodes nid200021 are ready for job
elvis@perlmutter-nid200021[~]$
Once you have an allocation copy the the node name starting with nid and go through the normal steps to connect to a remote ssh host using the hostname with nid as the hostname you want to connect to.
nid
nid