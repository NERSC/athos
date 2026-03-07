# Source: https://docs.nersc.gov/accounts/collaboration_accounts/

## Collaboration Accounts ¶


## Overview ¶

Most NERSC login accounts are associated with specific individuals and must not be shared. Sometimes it is advantageous to have a login account which is not tied to a person but instead to the group for the purposes of shared access to batch jobs or data. Collaboration Accounts are designed to facilitate collaborative computing by allowing multiple users to use the same account. All actions performed by the collaboration account are traceable back to the individual who used the collaboration account to perform those actions via gsisshd accounting logs. PIs and PI Proxies can request a collaboration account by submitting a ticket.

## Obtaining a Collaboration Account ¶

PIs or PI Proxies can request a collaboration account for their project by using the "Collaboration Account" form on the "Request Forms page" in the NERSC help portal (requires login).
Tip
Currently collaboration names must be limited to six characters.

## Logging Into Collaboration Accounts ¶


## Direct Login ¶

You can ssh directly to any NERSC system as your collaboration account by using sshproxy to generate an ssh key for the account
$ sshproxy -c your_collab_acct Password+OTP: Successfully obtained ssh key /Users/elvis/.ssh/your_collab_acct Key /Users/elvis/.ssh/your_collab_acct is valid: from 2025-01-16 09:46:00 -08:00 to 2025-01-17 09:47:58 -08:00
$ sshproxy -c your_collab_acct Password+OTP: Successfully obtained ssh key /Users/elvis/.ssh/your_collab_acct Key /Users/elvis/.ssh/your_collab_acct is valid: from 2025-01-16 09:46:00 -08:00 to 2025-01-17 09:47:58 -08:00
You can use this key to ssh (or scp, etc.) to any NERSC system, e.g.,
ssh -i $HOME/.ssh/your_collab_acct your_collab_acct@perlmutter.nersc.gov
ssh -i $HOME/.ssh/your_collab_acct your_collab_acct@perlmutter.nersc.gov

## Indirect Login ¶

You can also access your collaboration account if you've already logged in to a data transfer node (DTN), using:
$ collabsu <collaboration account name> <enter nersc password at the prompt>
$ collabsu <collaboration account name> <enter nersc password at the prompt>
Tip
Only your NERSC password is required for collabsu. You do not need your one-time password.
Please note, collabsu is not currently available on Perlmutter.
collabsu

## Controlling Collaboration Account Access ¶

Each collaboration account has two linux file groups associated with it, one with the same name as the collaboration account and one with the name c_<collaboration account> . PIs and PI Proxies can give users in their project access to the collaboration account by adding them to the c_<collaboration account> group in Iris .
c_<collaboration account>
c_<collaboration account>

## Transferring Data via Globus with a Collaboration Account ¶

At the request of the PI or PI Proxy, NERSC can set up a dedicated Globus endpoint that will allow data transfers via Globus as the collaboration account. This is a valuable tool for groups that need to make large data transfers into or out of NERSC and would like the data to be owned by the collaboration account. Only NERSC users who could already become the collaboration account and have linked their Globus account to their NERSC account are able to access these endpoints. If you are interested in this, please open a ticket and we'll work with you to set one up.

## Graphical User Interfaces on Perlmutter using Collaboration Accounts and ThinLinc ¶

Collaboration account access through ThinLinc is enabled by default. To change to the collaboration account, create an ssh key for the collaboration account and modify the ThinLinc settings to match the login setting for the account.
Server: thinlinc.nersc.gov
thinlinc.nersc.gov
User: Collaboration account name
Key: Path to the collaboration account ssh key

## Multiple Collaboration Account Desktops with ThinLinc ¶

Collaboration Accounts can open multiple desktop sessions using ThinLinc so that multiple users can have their own desktop. To get started with multiple desktops you will need to enable a setting in the ThinLinc client.
Click on "Advanced" button to get all the options
Click on "Options" button to open options window
Click on the "Advanced" tab at the top of the window
Under "Reconnect Policy"
Select "Always ask how multiple sessions should be handled"
Click "ok" to save your selection
Enter the connection details for ThinLinc

## Use Cases ¶


## Collaborative Data Management ¶

Large scale experimental and simulation data are typically read or written by multiple collaborators and are kept on disk for long periods. A problem that often arises is that the files are owned by the collaborator who did the work and if that collaborator changes roles the default Unix file permissions usually are such that the files cannot be managed (deleted) by other members of the collaboration and system administrators must be contacted. While the problem can be addressed with the appropriate use of Unix groups and file permissions in practice this tends to be problematic and a more seamless solution would be of great utility.

## Collaborative Software Management ¶

The issue with managing software is similar to that of managing data – different collaborators often need to work with the same files in a particular software installation and Unix groups and file permissions tend to be problematic for them. The main difference between collaborative data and software management is that software is typically managed on a short-term basis (hours/days) and smaller in size (~GBs) whereas production data is managed on a long-term basis (months/years) and much larger (~TBs to ~PBs).

## Collaborative Job Management ¶

Production level jobs are often run by a small team of collaborators. Project accounts would enable members of the team to manipulate jobs submitted by other team members as necessary.