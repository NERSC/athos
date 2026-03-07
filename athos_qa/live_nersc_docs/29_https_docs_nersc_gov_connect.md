# Source: https://docs.nersc.gov/connect/

## Establishing Connections ¶


## Perlmutter System Address ¶

Please make sure you have established a user account and have configured Multi-Factor Authentication (MFA) prior to login.
The Perlmutter system address used for connections is:
perlmutter.nersc.gov
perlmutter.nersc.gov
or
saul.nersc.gov
saul.nersc.gov

## NERSC IP Ranges ¶

Some institutions block outgoing connections except to a validated list of IPs. In order to access NERSC systems you will need to ensure the IP ranges in the table below are on the allowed list.
In this table, the "IP Range" column denotes the entire possible range of addresses that system could have. If you desire a shorter range, you can use the value in the "Current Used Range" column, but be advised that NERSC may change the IPs for nodes to anything within the broader range without notice.

## Connecting via SSH ¶

All NERSC computers (except HPSS) are reached using either the Secure Shell (SSH) communication and encryption protocol (version 2) or by Grid tools that use trusted certificates.
The Secure Shell (SSH) Protocol is a protocol for secure remote login and other secure network services over an insecure network. Among the most widely used implementations of SSH is OpenSSH . Users are strongly encouraged to use the most up-to-date versions of SSH clients that are available.
On a system with an SSH client installed, one can log in to the Perlmutter login nodes by running the following command in a terminal:
ssh <username>@perlmutter.nersc.gov   # or 'ssh <username>@saul.nersc.gov'
ssh <username>@perlmutter.nersc.gov   # or 'ssh <username>@saul.nersc.gov'
If the user has generated a temporary SSH key using sshproxy , then this command will connect the user to one of Perlmutter's login nodes. If the user has not generated a temporary SSH key, then SSH will challenge the user for their Iris password as well as their one-time password (OTP) before connecting them to a login node.
sshproxy
Typically systems will have multiple login nodes which sit behind a load balancer. New connections will be assigned a random node. If an account has recently connected the load balancer will attempt to connect to the same login node as the previous connection.
If you have configured sshproxy then you can run the following:
sshproxy
ssh -i ~/.ssh/nersc <user>@perlmutter.nersc.gov   # or 'ssh -i ~/.ssh/nersc <user>@saul.nersc.gov'
ssh -i ~/.ssh/nersc <user>@perlmutter.nersc.gov   # or 'ssh -i ~/.ssh/nersc <user>@saul.nersc.gov'
This assumes your identity file is in ~/.ssh/nersc . Using sshproxy allows for the convenience of having multiple SSH connections to the system without having to authenticate every time (for up to 24 hours).
~/.ssh/nersc
sshproxy
You can also connect to Perlmutter from a data transfer node (DTN) by logging into one of those nodes and then connecting to Perlmutter by running ssh perlmutter .
ssh perlmutter

## Connecting to Perlmutter with a Collaboration Account ¶

Please use the direct login functionality of sshproxy to log in to Perlmutter.
sshproxy

## SSH Certificate Authority ¶

NERSC generates SSH certificates for the primary login nodes using a NERSC SSH certificate authority. Most recent SSH clients support these certificates. You can add the following entry to the known_hosts file to make use of this certificate.
known_hosts
@cert-authority *.nersc.gov ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA2yKBpvRbdD9MWiu+7wg17vBsKy46AjjuL27DmdpDYiCqRE2mN0om9b0jn4eI91RGykbcRa9wUKJ2qaD0zsD08A8HM+R14H4UsZ5hi7S+xGqscJH7uTmXy5Igo5xEOahS9Z+ecgonDCgWKJnbd/FRu4vITYXrvTlIIGHGRBYj0GzbgLHBzedoMaGNRwhVyadH2SGRaZCgbH+Swevzy0GwYfZJA9zd7EX0jiAClkSYcflIOsygmI3gHv+b35mrvXcHDeQOR/wg8knfpSiFLCkVDpfgnj27Lemzxe6k61Brhv9CUiq+t7WApVDBovhdXZn6pBg+OKeDk1G1OLvRbxJ2bw==
@cert-authority *.nersc.gov ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA2yKBpvRbdD9MWiu+7wg17vBsKy46AjjuL27DmdpDYiCqRE2mN0om9b0jn4eI91RGykbcRa9wUKJ2qaD0zsD08A8HM+R14H4UsZ5hi7S+xGqscJH7uTmXy5Igo5xEOahS9Z+ecgonDCgWKJnbd/FRu4vITYXrvTlIIGHGRBYj0GzbgLHBzedoMaGNRwhVyadH2SGRaZCgbH+Swevzy0GwYfZJA9zd7EX0jiAClkSYcflIOsygmI3gHv+b35mrvXcHDeQOR/wg8knfpSiFLCkVDpfgnj27Lemzxe6k61Brhv9CUiq+t7WApVDBovhdXZn6pBg+OKeDk1G1OLvRbxJ2bw==

## Key Fingerprints ¶

NERSC may occasionally update the host keys on the major systems. Check this page to confirm the current fingerprints.
4096 SHA256:Db9s2Fa4J3qx7An5oIMgUqUAdK7UWJGTPGoIKD44+Gs perlmutter.nersc.gov (RSA)
4096 SHA256:Db9s2Fa4J3qx7An5oIMgUqUAdK7UWJGTPGoIKD44+Gs perlmutter.nersc.gov (RSA)
All of the data transfer nodes (DTNs) should have the same fingerprints:
4096 SHA256:ErZsheOUCZ4Plrk2KC7TTLyRFiBCDIHVxjiwnJDvztE dtn.nersc.gov (RSA)
256 SHA256:9zLgsb1cjyhr+YOkDhg/I8AWcJNJ1ME2j5YucHOUjyc dtn.nersc.gov (ECDSA)
256 SHA256:SOHXOjNaL4Rj98nX6rS0d9FGRRuqRZoKHrgfyjhuWEw dtn.nersc.gov (ED25519)
4096 SHA256:ErZsheOUCZ4Plrk2KC7TTLyRFiBCDIHVxjiwnJDvztE dtn.nersc.gov (RSA)
256 SHA256:9zLgsb1cjyhr+YOkDhg/I8AWcJNJ1ME2j5YucHOUjyc dtn.nersc.gov (ECDSA)
256 SHA256:SOHXOjNaL4Rj98nX6rS0d9FGRRuqRZoKHrgfyjhuWEw dtn.nersc.gov (ED25519)
3072 SHA256:18wXz/uzENow2+DaFSm7lmPgMzvkKsbzSJuuVFXgRZA thinlinc.nersc.gov (RSA)
256 SHA256:26RPCYxddertn0xqL0wsGrivsXrxZqqX9Mz00yJTe3A thinlinc.nersc.gov (ECDSA)
256 SHA256:boABAFxntxb47HgH+t3aWsahFkxhH2OFaDshyGzmpMU thinlinc.nersc.gov (ED25519)
3072 SHA256:18wXz/uzENow2+DaFSm7lmPgMzvkKsbzSJuuVFXgRZA thinlinc.nersc.gov (RSA)
256 SHA256:26RPCYxddertn0xqL0wsGrivsXrxZqqX9Mz00yJTe3A thinlinc.nersc.gov (ECDSA)
256 SHA256:boABAFxntxb47HgH+t3aWsahFkxhH2OFaDshyGzmpMU thinlinc.nersc.gov (ED25519)
Note
Scan for public keys on a NERSC host and generate their key fingerprints via: ssh-keygen -lf <(ssh-keyscan -t rsa,ed25519,ecdsa <NERSC hostname> 2>/dev/null) If you have already accepted public keys into your ~/.ssh/known_hosts file, verify their fingerprints via: ssh-keygen -lf ~/.ssh/known_hosts | grep <NERSC hostname>
ssh-keygen -lf <(ssh-keyscan -t rsa,ed25519,ecdsa <NERSC hostname> 2>/dev/null)
ssh-keygen -lf <(ssh-keyscan -t rsa,ed25519,ecdsa <NERSC hostname> 2>/dev/null)
~/.ssh/known_hosts
ssh-keygen -lf ~/.ssh/known_hosts | grep <NERSC hostname>
ssh-keygen -lf ~/.ssh/known_hosts | grep <NERSC hostname>
Note
Depending on the SSH client you use to connect to NERSC systems, you may see different key fingerprints. For example, PuTTY uses a different format of fingerprints (the md5 format instead of sha256) as follows:
Perlmutter
ssh-rsa 4096 3f:6b:e2:c7:95:36:ef:7c:ae:3f:be:1e:13:97:3b:08
ssh-rsa 4096 3f:6b:e2:c7:95:36:ef:7c:ae:3f:be:1e:13:97:3b:08
dtn[01-04]
ssh-ecdsa    256 5a:c0:06:ed:3c:28:6e:e1:30:ef:f8:8e:f3:0b:26:db
ssh-ed25519  256 65:06:f9:81:e6:21:3f:ab:67:d6:42:c0:eb:28:b4:69
ssh-rsa     4096 97:43:67:e9:13:99:6e:06:8c:26:5b:cd:7b:bc:06:bb
ssh-ecdsa    256 5a:c0:06:ed:3c:28:6e:e1:30:ef:f8:8e:f3:0b:26:db
ssh-ed25519  256 65:06:f9:81:e6:21:3f:ab:67:d6:42:c0:eb:28:b4:69
ssh-rsa     4096 97:43:67:e9:13:99:6e:06:8c:26:5b:cd:7b:bc:06:bb
You may see the following warning when connecting to Perlmutter with PuTTY, but it is safe to ingore.
PuTTY Security Alert
The server's host key is not cached in the registry. You have no guarantee that the server is the computer you think it is.
The server's rsa2 key fingerprint is:
ssh-rsa 4096 f6:36:aa:ed:60:9c:d5:f1:29:af:35:81:58:f6:26:45
If you trust this host, hit Yes to add the key to PuTTY's cache and carry on connecting.
If you want to carry on connecting just once, without adding the key to the cache, hit No.
If you do not trust this host, hit Cancel to abandon the connection.
PuTTY Security Alert
The server's host key is not cached in the registry. You have no guarantee that the server is the computer you think it is.
The server's rsa2 key fingerprint is:
ssh-rsa 4096 f6:36:aa:ed:60:9c:d5:f1:29:af:35:81:58:f6:26:45
If you trust this host, hit Yes to add the key to PuTTY's cache and carry on connecting.
If you want to carry on connecting just once, without adding the key to the cache, hit No.
If you do not trust this host, hit Cancel to abandon the connection.

## Host Keys ¶

These are the entries in ~/.ssh/known_hosts .
~/.ssh/known_hosts
perlmutter.nersc.gov ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDRDn86LRaU3Hl9E+OTwHtyLhLRvjNCF3e/LAuRu/Ms06FNsXTK1iIb3QMnWjzzFd4CwQwrKYZy9umHIJOyCW/SbEI4GRPrr7NJpVOvkGKVBqSo5aYY3LhqCqKgsX7lbnhwAyvYvHoy9qd/XyzjUMwvUYf1G0dmkIN4AGauEUysn2ixgfhi6+sODsLI9fNrZftnTpYecw2NPP7cn8Dwknh0Fw3450FaXZpUryghdsZp7VvtGwVjQYy5C2PFj8GKqoPh5pIrq4R63hx0OmQOQlRp8cSLtElx1vNzbTRMh43Te3/SJQ66h3sG8AgsPejJgPYEVKJhLpC8CQFj3mQFygcBcp5jOfNnEH2PWZ2Xmzi1p3qrtj01ZML6tIZX9GSdIPif0N2/Zi7+h2wsC+/d4gWdHwX0wQ+o3gYVCKl1Ipf3HJbQ+ZkJ+SecV81nWmu0sGP5nrKALYrQjSwsoO1yFxNhzFk0+XztFoSrMVsfLGG0n4ahTc/yJdB9/VL2/TcujiH+u64cDE9HhOw/JrHtUr13KC/0giaSc9qbjjdhKaXTDcdz4v9NCCqa6jb9R9+MDuufCJy/hOvvYqg99iCGAS+fKPvxJQ3byXOmzZ/dNVw0iz9jQdyTMISmn5BW23YQBtu9RbA8uvzhlV5vsTjtjadbVrWx4VEFgDLtBy8E0kACWw==
perlmutter.nersc.gov ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDRDn86LRaU3Hl9E+OTwHtyLhLRvjNCF3e/LAuRu/Ms06FNsXTK1iIb3QMnWjzzFd4CwQwrKYZy9umHIJOyCW/SbEI4GRPrr7NJpVOvkGKVBqSo5aYY3LhqCqKgsX7lbnhwAyvYvHoy9qd/XyzjUMwvUYf1G0dmkIN4AGauEUysn2ixgfhi6+sODsLI9fNrZftnTpYecw2NPP7cn8Dwknh0Fw3450FaXZpUryghdsZp7VvtGwVjQYy5C2PFj8GKqoPh5pIrq4R63hx0OmQOQlRp8cSLtElx1vNzbTRMh43Te3/SJQ66h3sG8AgsPejJgPYEVKJhLpC8CQFj3mQFygcBcp5jOfNnEH2PWZ2Xmzi1p3qrtj01ZML6tIZX9GSdIPif0N2/Zi7+h2wsC+/d4gWdHwX0wQ+o3gYVCKl1Ipf3HJbQ+ZkJ+SecV81nWmu0sGP5nrKALYrQjSwsoO1yFxNhzFk0+XztFoSrMVsfLGG0n4ahTc/yJdB9/VL2/TcujiH+u64cDE9HhOw/JrHtUr13KC/0giaSc9qbjjdhKaXTDcdz4v9NCCqa6jb9R9+MDuufCJy/hOvvYqg99iCGAS+fKPvxJQ3byXOmzZ/dNVw0iz9jQdyTMISmn5BW23YQBtu9RbA8uvzhlV5vsTjtjadbVrWx4VEFgDLtBy8E0kACWw==

## Troubleshooting ¶


## "Access Denied", "Permission Denied" or "Too many authentication failures" ¶

Common causes of these are:
You are using your laptop username instead of your NERSC username (SSH will by default assume that your remote (NERSC) username is the same as your local (laptop) one). You can avoid this by:
Passing your NERSC username explicitly, for example if your NERSC username is elvis : ssh -u elvis perlmutter.nersc.gov , or ssh elvis@perlmutter.nersc.gov
elvis
ssh -u elvis perlmutter.nersc.gov , or
ssh -u elvis perlmutter.nersc.gov
ssh elvis@perlmutter.nersc.gov
ssh elvis@perlmutter.nersc.gov
Specifying your NERSC username in your laptop $HOME/.ssh/config file, e.g., Host perlmutter
  Hostname perlmutter.nersc.gov
  User elvis
Specifying your NERSC username in your laptop $HOME/.ssh/config file, e.g.,
$HOME/.ssh/config
Host perlmutter
  Hostname perlmutter.nersc.gov
  User elvis
Host perlmutter
  Hostname perlmutter.nersc.gov
  User elvis
You mistyped or forgot your password. Check that you have the correct password by logging in to Iris . Logging into Iris also clears authentication failures, in the event that too many failed authentication attempts have prompted the system to lock your account.
You mistyped or forgot your password. Check that you have the correct password by logging in to Iris . Logging into Iris also clears authentication failures, in the event that too many failed authentication attempts have prompted the system to lock your account.
You are using PuTTY or MobaXterm and the NERSC system you want is currently unavailable (these Windows SSH clients are known to not display the pre-authentication banners which NERSC uses to indicate down status). You can check the system status on the [NERSC Center Status page]( https://www.nersc.gov/users/status .
You are using PuTTY or MobaXterm and the NERSC system you want is currently unavailable (these Windows SSH clients are known to not display the pre-authentication banners which NERSC uses to indicate down status). You can check the system status on the [NERSC Center Status page]( https://www.nersc.gov/users/status .
You have many SSH keys in your keychain or SSH agent, and your SSH client is trying them all one at a time. After too many wrong ones are tried in a row, the SSH server will stop accepting further attempts. You can check if this might be the cause by adding -vv to your ssh command and look for failed authentication attempts in the output, eg ssh -vv elvis@perlmutter.nersc.gov . If this might be the cause, you can instruct your laptop SSH client to only use a specific identity, for example: ssh -o IdentitiesOnly=yes -i ~/.ssh/nersc elvis@perlmutter.nersc.gov if you are using sshproxy (the identity sshproxy generates is called nersc ), or ssh -o IdentitiesOnly=yes -i ~/.ssh/id.rsa elvis@perlmutter.nersc.gov if you are not.
You have many SSH keys in your keychain or SSH agent, and your SSH client is trying them all one at a time. After too many wrong ones are tried in a row, the SSH server will stop accepting further attempts. You can check if this might be the cause by adding -vv to your ssh command and look for failed authentication attempts in the output, eg ssh -vv elvis@perlmutter.nersc.gov . If this might be the cause, you can instruct your laptop SSH client to only use a specific identity, for example:
-vv
ssh
ssh -vv elvis@perlmutter.nersc.gov
ssh -o IdentitiesOnly=yes -i ~/.ssh/nersc elvis@perlmutter.nersc.gov if you are using sshproxy (the identity sshproxy generates is called nersc ), or
ssh -o IdentitiesOnly=yes -i ~/.ssh/nersc elvis@perlmutter.nersc.gov
sshproxy
sshproxy
nersc
ssh -o IdentitiesOnly=yes -i ~/.ssh/id.rsa elvis@perlmutter.nersc.gov if you are not.
ssh -o IdentitiesOnly=yes -i ~/.ssh/id.rsa elvis@perlmutter.nersc.gov
If you are still unable to login, contact NERSC Account Support at accounts@nersc.gov .

## Host Authenticity ¶

This message may appear when a connection to a new machine is first established:
The authenticity of host 'perlmutter.nersc.gov' can't be established.
RSA key fingerprint is <omitted>
Are you sure you want to continue connecting (yes/no)?
The authenticity of host 'perlmutter.nersc.gov' can't be established.
RSA key fingerprint is <omitted>
Are you sure you want to continue connecting (yes/no)?
Check that the fingerprints match the list above .
If they match, accept.
If they do not match, let us know .

## Host Identification Changed ¶

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
...
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
...
Ensure that your ~/.ssh/known_hosts file contains the correct entries for the host and confirm the fingerprints using the posted fingerprints above. Add the certificate authority line to your known_hosts file if you version of ssh supports SSH certificates.
~/.ssh/known_hosts
known_hosts
Open ~/.ssh/known_hosts
~/.ssh/known_hosts
Remove any lines referring the host in question and save the file
Paste the host key entries from above or retry connecting to the host and accept the new host key after verify that you have the correct "fingerprint" from the above list.

## SSH Connections Disconnect Periodically ¶

Some users experience their SSH or Globus connections to NERSC systems disconnect periodically and somewhat randomly. One cause of this is due to a user's SSH client using jumbo Ethernet frames , while a network switch or router between the user's computer and the NERSC network is configured not to forward jumbo frames, e.g., a home WiFi router or a router maintained by an institution's IT division.
Users who experience intermittent failures of their SSH connections to NERSC systems are encouraged to read the detailed description of the jumbo frame problem by ESnet.

## Host Key Errors ¶

An error about host keys indicates that the SSH client being used is too old and it is incompatible with NERSC systems. This error manifests as "Couldn't agree a host key algorithm ((available: rsa-sha2-512,rsa-sha2-256))" (or similar) in PuTTY, or "no matching host key type found" in MobaXterm. Update to the latest version of the software to eliminate this issue.

## Other SSH Connection Failures ¶

If users encounter unexpected failures when attempting to establish SSH connections to NERSC systems, they are encouraged to collect verbose output from the SSH client where possible, and provide that output in a ticket submitted via the NERSC Help Portal . If using a variant of OpenSSH, verbose output can be obtained by adding the -vvv flag to the ssh command. Other SSH clients may have other ways of emitting verbose output, and users are encouraged to consult the relevant documentation for obtaining such output.
-vvv
ssh