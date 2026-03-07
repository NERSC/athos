# Source: https://docs.nersc.gov/systems/perlmutter/timeline/

## Perlmutter Timeline ¶

This page records a brief timeline of significant events and user environment changes on Perlmutter. Please see our current known issues page for a list of known issues on Perlmutter.

## March 4, 2026 ¶

Rolling reboot to deploy a Lustre client upgrade to 2.15.7 to address an issue with ACLs. Compute nodes were rebooted after their jobs ended. Login nodes, slurm commands, and the scratch file system remained available.

## February 19, 2026 ¶

Updates to improve system stability and performance: Operating system to COS 3.3 (SLES 15 SP6). NVIDIA GPU driver to 580.105.08 Upgrade to USS 1.3 Upgrade to CSM 1.6 Slurm build and configuration update. Numerous fixes to hardware.
Operating system to COS 3.3 (SLES 15 SP6).
NVIDIA GPU driver to 580.105.08
Upgrade to USS 1.3
Upgrade to CSM 1.6
Slurm build and configuration update.
Numerous fixes to hardware.
Add express_amsc QOS
User software environment updates: The programming environment has been updated to CPE 25.09. See the CPE 25.09 release notes for a full list of changes. Notable updates: gcc 14.3.0 cray-mpich 9.0.1 (based on MPICH 4.1.2) Default cudatoolkit module version updated to 12.9 Removed CPE 23.02, 23.05, and 23.09
The programming environment has been updated to CPE 25.09. See the CPE 25.09 release notes for a full list of changes. Notable updates: gcc 14.3.0 cray-mpich 9.0.1 (based on MPICH 4.1.2)
gcc 14.3.0
cray-mpich 9.0.1 (based on MPICH 4.1.2)
Default cudatoolkit module version updated to 12.9
Removed CPE 23.02, 23.05, and 23.09
NERSC module updates: conda: add Miniforge3-25.11.0-1 (new default) espresso: fix ESPRESSO_PSEUDO paths hip: deprecate 5.5 intel: remove 2024.1.0 (SYCL plugin no longer maintained) kokkos: deprecate 4.3.00 llvm: add 21.1.4 nccl: add 2.29.2-cu13 numba-cuda-580-patch: add new module openmpi: add 5.0.8 PrgEnv-llvm: add 21.1.4 python: add new environments for python 3.12 and 3.13 (new default) pytorch: deprecate 2.6.0; add 2.6.0-1; update 2.6.0 (add MKL LD_PRELOAD libs) qchem: add 6.3.0 spack-config: remove main spack: make 1.1.0 the new default
conda: add Miniforge3-25.11.0-1 (new default)
espresso: fix ESPRESSO_PSEUDO paths
hip: deprecate 5.5
intel: remove 2024.1.0 (SYCL plugin no longer maintained)
kokkos: deprecate 4.3.00
llvm: add 21.1.4
nccl: add 2.29.2-cu13
numba-cuda-580-patch: add new module
openmpi: add 5.0.8
PrgEnv-llvm: add 21.1.4
python: add new environments for python 3.12 and 3.13 (new default)
pytorch: deprecate 2.6.0; add 2.6.0-1; update 2.6.0 (add MKL LD_PRELOAD libs)
qchem: add 6.3.0
spack-config: remove main
spack: make 1.1.0 the new default

## January 21, 2026 ¶

Slurm accounts and user associations were updated to reflect the new allocation year.
Updates to improve system stability and performance: Neo, the file system control software for Perlmutter scratch, was updated to 7.2-030. Numerous fixes to hardware
Neo, the file system control software for Perlmutter scratch, was updated to 7.2-030.
Numerous fixes to hardware

## December 17, 2025 ¶

Queue configuration changes: New limited time holiday queue added with a lower charge and reduced starting priority For a limited time, overrun jobs are no longer subject to pre-emption
New limited time holiday queue added with a lower charge and reduced starting priority
For a limited time, overrun jobs are no longer subject to pre-emption
Updates to improve system stability and performance: Update slurm to 24.11.7 slurm configuration update, including support for topology-aware scheduling patch to replace a confusing message for pending jobs with Resources drop previous debugging patch for a now solved issue Update gpfs to 5.2.3-4 Fix shifterimg pulling issues on SLE 15 SP6 Update cvmfs to 2.13.3 Add cuda compat lib 13.0 Numerous fixes to hardware
Update slurm to 24.11.7 slurm configuration update, including support for topology-aware scheduling patch to replace a confusing message for pending jobs with Resources drop previous debugging patch for a now solved issue
slurm configuration update, including support for topology-aware scheduling
patch to replace a confusing message for pending jobs with Resources
drop previous debugging patch for a now solved issue
Update gpfs to 5.2.3-4
Fix shifterimg pulling issues on SLE 15 SP6
Update cvmfs to 2.13.3
Add cuda compat lib 13.0
Numerous fixes to hardware
NERSC module updates: cudatoolkit: add 13.0 nvidia: add 25.9 fpm: remove 0.9.0, 0.10.0, 0.10.1 llvm: move the nightly build installation path openmpi: remove 5.0.0, 5.0.0rc12 and 5.0.3 spack: add 1.1.0; remove 0.22, 0.23.0
cudatoolkit: add 13.0
nvidia: add 25.9
fpm: remove 0.9.0, 0.10.0, 0.10.1
llvm: move the nightly build installation path
openmpi: remove 5.0.0, 5.0.0rc12 and 5.0.3
spack: add 1.1.0; remove 0.22, 0.23.0

## November 12, 2025 ¶

Updates to improve system stability and performance: Update to slurm to improve database performance and fix an issue that sometimes resulted in ineligible nodes being selected for certain user reservations Numerous fixes to hardware.
Update to slurm to improve database performance and fix an issue that sometimes resulted in ineligible nodes being selected for certain user reservations
Numerous fixes to hardware.
NERSC module updates: conda: add Miniforge3-25.9.1-0 cudatoolkit: deprecate 12.0 julia: remove 1.8 and 1.9; upgrade 1.10.9 => 1.10.10, 1.11.4 => 1.11.7; and add 1.12.1 juliaup: upgrade 1.17.21 => 1.18.9 nvidia: deprecate 23.1
conda: add Miniforge3-25.9.1-0
cudatoolkit: deprecate 12.0
julia: remove 1.8 and 1.9; upgrade 1.10.9 => 1.10.10, 1.11.4 => 1.11.7; and add 1.12.1
juliaup: upgrade 1.17.21 => 1.18.9
nvidia: deprecate 23.1

## October 15, 2025 ¶

Updates to improve system stability and performance: Improvements and fixes to DVS Slingshot updated to version 2.3.1
Improvements and fixes to DVS
Slingshot updated to version 2.3.1
NERSC module updates: cpe: deprecate old CPEs cudatoolkit: deprecate 11.7 nvidia: deprecate 22.7 pytorch: add 2.8.0 spack: add 0.23.1, 1.0.2 (new default). deprecate 0.22, 0.23.0 spack-config: add 25.10.0 (new default). deprecate main
cpe: deprecate old CPEs
cudatoolkit: deprecate 11.7
nvidia: deprecate 22.7
pytorch: add 2.8.0
spack: add 0.23.1, 1.0.2 (new default). deprecate 0.22, 0.23.0
spack-config: add 25.10.0 (new default). deprecate main

## September 25, 2025 ¶

Improved the cgroups process control algorithm on the login nodes by raising the maximum number of user sessions and removing a parameter that was over throttling user sessions close to the resource limits. This is intended to improve the responsiveness of the login nodes.

## September 17, 2025 ¶

Perlmutter logins, Scratch File System, and Slurm remained available with short interruptions.
Rolling reboot that began on September 15, 2025 finished.
Updates to improve system stability: Slurm configuration update. Numerous fixes to hardware.
Slurm configuration update.
Numerous fixes to hardware.

## September 15, 2025 ¶

Began rolling reboot of compute nodes to change the LDMS configuration file to add the job ID to a few metrics. This reboot will finish after September 17, 2025.

## August 20, 2025 ¶

Updates to improve system stability and performance: Upgrade Slingshot Host Software to version 12.0.2-68. Switch service nodes to using 4 NUMA domains per socket. This is intended to improve stability when accessing NERSC Global File Systems.
Upgrade Slingshot Host Software to version 12.0.2-68.
Switch service nodes to using 4 NUMA domains per socket. This is intended to improve stability when accessing NERSC Global File Systems.
NERSC module updates: evp-patch: remove module nccl: remove 2.15.5-ofi nccl for podman-hpc and shifter: retire 2.15 nccl for podman-hpc: update plugin to use 2.19 tensorflow: remove 2.9.0
evp-patch: remove module
nccl: remove 2.15.5-ofi
nccl for podman-hpc and shifter: retire 2.15
nccl for podman-hpc: update plugin to use 2.19
tensorflow: remove 2.9.0

## July 23, 2025 ¶

Updates to improve system stability: Neo, the file system control software for Perlmutter scratch, was updated to 7.1. Lustre clients were upgraded to 2.15.6. GPFS version upgraded to 5.2.3.1. Slurm upgraded to 24.11.6. Slurm update to better isolate jobs on shared nodes. Shifter updated to improve after-job cleanup. Numerous fixes to hardware.
Neo, the file system control software for Perlmutter scratch, was updated to 7.1. Lustre clients were upgraded to 2.15.6.
GPFS version upgraded to 5.2.3.1.
Slurm upgraded to 24.11.6.
Slurm update to better isolate jobs on shared nodes.
Shifter updated to improve after-job cleanup.
Numerous fixes to hardware.
NERSC module updates: codee: remove 2025.2.2, 2025.2.3, 2025.2.4, default due to an expired license cudatoolkit: add 12.9 fpm: add 0.11.0, 0.12.0; deprecate 0.9.0, 0.10.0, 0.10.1 intel: update 2024.1.0 mpich: add 4.3.0; deprecate 4.1.1; remove 4.2.2 nvidia: add 25.5 PrgEnv-llvm: add 2.0; deprecate 0.1, 0.5 tensorflow: deprecate 2.9.0 nccl: deprecate 2.15.5-ofi
codee: remove 2025.2.2, 2025.2.3, 2025.2.4, default due to an expired license
cudatoolkit: add 12.9
fpm: add 0.11.0, 0.12.0; deprecate 0.9.0, 0.10.0, 0.10.1
intel: update 2024.1.0
mpich: add 4.3.0; deprecate 4.1.1; remove 4.2.2
nvidia: add 25.5
PrgEnv-llvm: add 2.0; deprecate 0.1, 0.5
tensorflow: deprecate 2.9.0
nccl: deprecate 2.15.5-ofi

## June 18, 2025 ¶

Updates to improve system stability: Updated NVIDIA driver to version 550.163.01 Enabled persistent mode in GDRCopy v2.4.4 Upgraded HPSS client to version 2025.06 to address edge cases causing data read corruption Applied patches to Slurm 24.11.5: Fixed an issue with --signal usage Resolved an edge case when changing the QoS of allocated jobs Improved step manager functionality Provided more informative user messages when parts of Slurm are down Fixed symlink issues under /usr/bin that caused errors in Spack when scanning for installed system packages Added a feature to the Slurm job submit filter to ensure GPU requests align with requested memory and CPUs Set the default MPICH_MPIIO_DVS_MAXNODES to 48 to reflect the addition of 24 new DVS gateway nodes Upgraded nersc-pymon to version 0.3.0 for improved Python module usage tracking
Updated NVIDIA driver to version 550.163.01
Enabled persistent mode in GDRCopy v2.4.4
Upgraded HPSS client to version 2025.06 to address edge cases causing data read corruption
Applied patches to Slurm 24.11.5: Fixed an issue with --signal usage Resolved an edge case when changing the QoS of allocated jobs Improved step manager functionality Provided more informative user messages when parts of Slurm are down
Fixed an issue with --signal usage
--signal
Resolved an edge case when changing the QoS of allocated jobs
Improved step manager functionality
Provided more informative user messages when parts of Slurm are down
Fixed symlink issues under /usr/bin that caused errors in Spack when scanning for installed system packages
/usr/bin
Added a feature to the Slurm job submit filter to ensure GPU requests align with requested memory and CPUs
Set the default MPICH_MPIIO_DVS_MAXNODES to 48 to reflect the addition of 24 new DVS gateway nodes
MPICH_MPIIO_DVS_MAXNODES
Upgraded nersc-pymon to version 0.3.0 for improved Python module usage tracking
User software environment updates: Updated fuse-overlay to fix issues with complex container image builds using podman-hpc Added CVMFS repositories for the Dark Energy Survey NERSC module updates: codee: Added versions 2025.2.3 and 2025.2.4 (new default); removed 2025.2 and 2025.2.1 forge: Added version 24.1.3 (new default); removed 24.1 pytorch: Removed versions 1.13.1, 2.0.1, 2.1.0-cu12, and 2.3.1 totalview: Added version 2025.2.6 (new default); removed 2024.3.10
Updated fuse-overlay to fix issues with complex container image builds using podman-hpc
podman-hpc
Added CVMFS repositories for the Dark Energy Survey
NERSC module updates: codee: Added versions 2025.2.3 and 2025.2.4 (new default); removed 2025.2 and 2025.2.1 forge: Added version 24.1.3 (new default); removed 24.1 pytorch: Removed versions 1.13.1, 2.0.1, 2.1.0-cu12, and 2.3.1 totalview: Added version 2025.2.6 (new default); removed 2024.3.10
codee: Added versions 2025.2.3 and 2025.2.4 (new default); removed 2025.2 and 2025.2.1
forge: Added version 24.1.3 (new default); removed 24.1
pytorch: Removed versions 1.13.1, 2.0.1, 2.1.0-cu12, and 2.3.1
totalview: Added version 2025.2.6 (new default); removed 2024.3.10

## May 21, 2025 ¶

Jupyter: update JupyterHub to version 5.3
Updates to improve system stability and performance: Upgrade to Slurm 24.11.5. Update GPFS to 5.2.3.0. This is intended to address an issue that led to login nodes intermittently crashing. Add a way to disable transparent huge pages in users' jobs
Upgrade to Slurm 24.11.5.
Update GPFS to 5.2.3.0. This is intended to address an issue that led to login nodes intermittently crashing.
Add a way to disable transparent huge pages in users' jobs
NERSC module updates: codee: add 2025.2, 2025.2.1 and 2025.2.2 (new default); remove 2025.1, 2025.1.2 and 2025.1.3 julia: add 1.10.9, latest (loading the latest module will give access to modules for experimental julia installs) juliaup: stable now depends on the cudatoolkit module llvm: add 20.1.3 parallel: remove deprecated module
codee: add 2025.2, 2025.2.1 and 2025.2.2 (new default); remove 2025.1, 2025.1.2 and 2025.1.3
julia: add 1.10.9, latest (loading the latest module will give access to modules for experimental julia installs)
latest
juliaup: stable now depends on the cudatoolkit module
llvm: add 20.1.3
parallel: remove deprecated module

## April 16, 2025 ¶

Temporary change of default shared memory mode from XPMEM to CMA to address an ongoing issue causing node failures. If needed, users can request XPMEM mode explicitly
XPMEM
CMA
XPMEM
Deployed slurm license integration for MATLAB and IDL. This is intended to keep jobs using these services from starting if a license is not available. Please see the license documentation for details
Fix a misconfiguration in the network fabric between Perlmutter and the NERSC Global File Systems (homes, global common, and CFS). This is intended to improve file system performance
Numerous updates to improve system stability: Upgrade to Slurm 24.11.4 Update to Slingshot 2.3. Upgrade to CSM 1.5.4 Upgrade to USS 1.1.2, COS 3.1.2 Upgrade the firmware to HFP 25.2.1
Upgrade to Slurm 24.11.4
Update to Slingshot 2.3.
Upgrade to CSM 1.5.4
Upgrade to USS 1.1.2, COS 3.1.2
Upgrade the firmware to HFP 25.2.1
User software environment updates: juliaup: add stable version alias; julia: add 1.11.4, remove 1.10.4, make all julia modules depend on the juliaup module totalview: add 2025.1.13 (new default); remove 2024.2.11
juliaup: add stable version alias;
julia: add 1.11.4, remove 1.10.4, make all julia modules depend on the juliaup module
totalview: add 2025.1.13 (new default); remove 2024.2.11

## March 26, 2025 ¶

Upgrade the network fabric that connects the Global Homes, Global Common, and Community File Systems to other systems to use RDMA over Converged Ethernet (RoCE). This is intended to improve bandwidth and network speed capabilities.
Doubled the number of gateway nodes serving DVS, the I/O forwarding service that delivers the Global Homes, Global Common, and Community File Systems.
Upgrade Slurm to version 24.11.3
Jupyter: add warning banner for impending login node shutdown and batch job ending
User software environment updates: Configure nvidia/24.5 nvc++ compiler to use g++ 13 header files and STL. Earlier nvidia module versions will continue to use g++ 7 Backport fix for gcc-native/12.3 to add gcc 12 compilers to PATH NERSC module updates: climate-utils: remove 2023q2, 2023q2-old codee: add 2025.1.2, 2025.1.3 (new default); remove 2024.4.3, 2024.4.5 cudnn: add 9.5.0 darshan: update default (add cray-mpich prereq) evp-patch: deprecate module (issue fixed, no longer needed) forge: add 24.1.2 (new default); remove 24.0.5 mpich: update all (add PKG_CONFIG_PATH) nccl: add 2.24.3 nvshmem: add 3.2.5-1 openmpi: add 5.0.7; deprecate 5.0.0rc12, 5.0.0, 5.0.3; update all (add PKG_CONFIG_PATH) python: add 3.12, 3.13 pytorch: add 2.6.0 R: remove 4.2.3 rust: add stable vasp: update 6.4.2-gpu, 6.4.3-gpu (add dependency on nccl/2.18.3-cu12) vasp-tpc: update 6.4.2-gpu (add dependency on nccl/2.18.3-cu12)
Configure nvidia/24.5 nvc++ compiler to use g++ 13 header files and STL. Earlier nvidia module versions will continue to use g++ 7
Backport fix for gcc-native/12.3 to add gcc 12 compilers to PATH
NERSC module updates: climate-utils: remove 2023q2, 2023q2-old codee: add 2025.1.2, 2025.1.3 (new default); remove 2024.4.3, 2024.4.5 cudnn: add 9.5.0 darshan: update default (add cray-mpich prereq) evp-patch: deprecate module (issue fixed, no longer needed) forge: add 24.1.2 (new default); remove 24.0.5 mpich: update all (add PKG_CONFIG_PATH) nccl: add 2.24.3 nvshmem: add 3.2.5-1 openmpi: add 5.0.7; deprecate 5.0.0rc12, 5.0.0, 5.0.3; update all (add PKG_CONFIG_PATH) python: add 3.12, 3.13 pytorch: add 2.6.0 R: remove 4.2.3 rust: add stable vasp: update 6.4.2-gpu, 6.4.3-gpu (add dependency on nccl/2.18.3-cu12) vasp-tpc: update 6.4.2-gpu (add dependency on nccl/2.18.3-cu12)
climate-utils: remove 2023q2, 2023q2-old
codee: add 2025.1.2, 2025.1.3 (new default); remove 2024.4.3, 2024.4.5
cudnn: add 9.5.0
darshan: update default (add cray-mpich prereq)
evp-patch: deprecate module (issue fixed, no longer needed)
forge: add 24.1.2 (new default); remove 24.0.5
mpich: update all (add PKG_CONFIG_PATH)
nccl: add 2.24.3
nvshmem: add 3.2.5-1
openmpi: add 5.0.7; deprecate 5.0.0rc12, 5.0.0, 5.0.3; update all (add PKG_CONFIG_PATH)
python: add 3.12, 3.13
pytorch: add 2.6.0
R: remove 4.2.3
rust: add stable
vasp: update 6.4.2-gpu, 6.4.3-gpu (add dependency on nccl/2.18.3-cu12)
vasp-tpc: update 6.4.2-gpu (add dependency on nccl/2.18.3-cu12)

## February 19, 2025 ¶

Numerous updates intended to improve system stability: Operating system has been updated to COS 3.1 (SLES 15 SP5). Adjust memory limits for new SP5 kernel Update gdrcopy to 2.4.4 Update cvmfs to 2.12.6 Change DVS server settings (reducing conns_per_peer from 8 to 1) in order to improve DVS stability.
Operating system has been updated to COS 3.1 (SLES 15 SP5).
Adjust memory limits for new SP5 kernel
Update gdrcopy to 2.4.4
Update cvmfs to 2.12.6
Change DVS server settings (reducing conns_per_peer from 8 to 1) in order to improve DVS stability.
conns_per_peer
User software environment updates: The programming environment has been updated to CPE 24.07. See the CPE 24.07 release notes for a full list of changes. Notable updates: GCC 13.2 Cray MPICH 8.1.30 HDF5 1.14.3.1 Parallel NetCDF 1.12.3.13 Default cudatoolkit module version updated to cudatoolkit/12.4
The programming environment has been updated to CPE 24.07. See the CPE 24.07 release notes for a full list of changes. Notable updates: GCC 13.2 Cray MPICH 8.1.30 HDF5 1.14.3.1 Parallel NetCDF 1.12.3.13 Default cudatoolkit module version updated to cudatoolkit/12.4
GCC 13.2
Cray MPICH 8.1.30
HDF5 1.14.3.1
Parallel NetCDF 1.12.3.13
Default cudatoolkit module version updated to cudatoolkit/12.4
NERSC module updates: climate-utils: add 2025.01 (new default), hide 2023q2-old codee: add 2024.4.5 and 2025.1 (new default), remove 2024.4.1 and 2024.4.2 conda: add Miniforge3-24.11.3-0, remove non-Miniforge3 variants darshan: add version named "default" (new default) forge: update 24.1.1, 24.1 and 24.0.5 parallel: deprecate module (GNU parallel has been added to the base image) R: deprecate 4.2.3
climate-utils: add 2025.01 (new default), hide 2023q2-old
codee: add 2024.4.5 and 2025.1 (new default), remove 2024.4.1 and 2024.4.2
conda: add Miniforge3-24.11.3-0, remove non-Miniforge3 variants
darshan: add version named "default" (new default)
forge: update 24.1.1, 24.1 and 24.0.5
parallel: deprecate module (GNU parallel has been added to the base image)
R: deprecate 4.2.3

## January 15, 2025 ¶

Upgraded the GPU driver to 550.127.08.
Slingshot Host Software updated to 11.0.2. This is intended to address an issue with the retry handler that caused large scale I/O to fail.
Slingshot fabric rebuild. This is intended to increase network stability and performance.
Allocation year rollover, majority of activities are defined in the specific AY rollover page
NERSC module updates: berkeleygw: remove 3.0.1-cpu, 3.0.1-gpu cmake: update 3.24.3 install path codee: add 2024.4.2 and 2024.4.3 (new default); remove 2024.3.5 and 2024.4 conda: deprecate non-Miniforge3 variants, set Miniforge3-24.7.1-0 as new default cpu: remove redundant module unload darshan: add 3.4.6 (new default) e4s: remove 23.08 eigen: remove 3.4.0 espresso: remove 7.0-libxc-5.2.2-cpu, 7.0-libxc-5.2.2-gpu, 7.1-libxc-6.1.0-cpu fast-mkl-amd: update install path forge: add 24.1.1 (new default); remove 24.0.3 gpu: remove redundant module unload gromacs: remove 2021.5-plumed, 2021.5, 2022.3-gpu idl: update install path julia: remove 1.10.0, 1.10.1, 1.10.2, 1.10.3 math-libs-real32: remove 2023q2 mathematica: update install path mumps: remove 5.5.1-gcc-11.2.0 mvasp: remove 5.4.4-cpu nersc-default: add new defaults module nersc_cr: remove 23.06 petsc: remove 3.19.3-cpu-complex python: remove evp-patch dependency, remove 3.9-anaconda-2021.11 R: add 4.3.3 spack: remove develop, e4s-23.08 texlive: add 2024; remove 2022 vasp: remove 5.4.1-cpu, 6.2.1-gpu, 6.3.2-cpu, 6.3.2-gpu, 6.4.1-cpu, 6.4.1-gpu vasp-tpc: remove 6.2.1-gpu, 6.3.2-cpu, 6.3.2-gpu wannier90: remove 3.1.0-gnu, 3.1.0-nvidia, 3.1.0
berkeleygw: remove 3.0.1-cpu, 3.0.1-gpu
cmake: update 3.24.3 install path
codee: add 2024.4.2 and 2024.4.3 (new default); remove 2024.3.5 and 2024.4
conda: deprecate non-Miniforge3 variants, set Miniforge3-24.7.1-0 as new default
cpu: remove redundant module unload
darshan: add 3.4.6 (new default)
e4s: remove 23.08
eigen: remove 3.4.0
espresso: remove 7.0-libxc-5.2.2-cpu, 7.0-libxc-5.2.2-gpu, 7.1-libxc-6.1.0-cpu
fast-mkl-amd: update install path
forge: add 24.1.1 (new default); remove 24.0.3
gpu: remove redundant module unload
gromacs: remove 2021.5-plumed, 2021.5, 2022.3-gpu
idl: update install path
julia: remove 1.10.0, 1.10.1, 1.10.2, 1.10.3
math-libs-real32: remove 2023q2
mathematica: update install path
mumps: remove 5.5.1-gcc-11.2.0
mvasp: remove 5.4.4-cpu
nersc-default: add new defaults module
nersc_cr: remove 23.06
petsc: remove 3.19.3-cpu-complex
python: remove evp-patch dependency, remove 3.9-anaconda-2021.11
R: add 4.3.3
spack: remove develop, e4s-23.08
texlive: add 2024; remove 2022
vasp: remove 5.4.1-cpu, 6.2.1-gpu, 6.3.2-cpu, 6.3.2-gpu, 6.4.1-cpu, 6.4.1-gpu
vasp-tpc: remove 6.2.1-gpu, 6.3.2-cpu, 6.3.2-gpu
wannier90: remove 3.1.0-gnu, 3.1.0-nvidia, 3.1.0

## December 18, 2024 ¶

Numerous updates intended to improve system stability and performance: Upgrade BIOS and ILO on Service nodes to HFP 24.09. Disable NAPI threading on gateway nodes. This is intended to improve stability of DVS. Switch E1000 nodes to ksocklnd conns_per_peer=1. This is intended to improve stability of the lustre file system. Update cvmfs to 2.11.5. Update podman to 5.3.1. Update podman-hpc to 1.1.2 to fix various issues with migrated images, improve shared run startup time, and add convenience modules for volume mounts. Improve response time for sacct queries with --state pending .
Upgrade BIOS and ILO on Service nodes to HFP 24.09.
Disable NAPI threading on gateway nodes. This is intended to improve stability of DVS.
Switch E1000 nodes to ksocklnd conns_per_peer=1. This is intended to improve stability of the lustre file system.
Update cvmfs to 2.11.5.
Update podman to 5.3.1.
Update podman-hpc to 1.1.2 to fix various issues with migrated images, improve shared run startup time, and add convenience modules for volume mounts.
Improve response time for sacct queries with --state pending .
sacct
--state pending
NERSC module updates: climate-utils: change the deprecation message for 2023q2 cmake: deprecate 3.24.3 codee: remove 2024.2.6, 2024.3.1 and 2024.3.4; add 2024.3.5, 2024.4 and 2024.4.1 (new default) e4s: deprecate 23.08 forge: remove 24.0.2 and add 24.1 (new default) jamo: set prod as default version, fix python-jamo prereq matlab: update to new install paths nccl: move 2.18 to new install path, remove 2.14.3 python: deprecate 3.9-anaconda-2021.11 pytorch: remove evp-patch dependency, move 2.0 and 2.1 to new install paths spack: add 0.23.0, deprecate e4s-23.08 spack-config: add main tensorflow: remove evp-patch dependency totalview: remove 2024.1.21 and add 2024.4.2 (new default) vasp-tpc: deprecate 6.3.2-gpu
climate-utils: change the deprecation message for 2023q2
cmake: deprecate 3.24.3
codee: remove 2024.2.6, 2024.3.1 and 2024.3.4; add 2024.3.5, 2024.4 and 2024.4.1 (new default)
e4s: deprecate 23.08
forge: remove 24.0.2 and add 24.1 (new default)
jamo: set prod as default version, fix python-jamo prereq
matlab: update to new install paths
nccl: move 2.18 to new install path, remove 2.14.3
python: deprecate 3.9-anaconda-2021.11
pytorch: remove evp-patch dependency, move 2.0 and 2.1 to new install paths
spack: add 0.23.0, deprecate e4s-23.08
spack-config: add main
tensorflow: remove evp-patch dependency
totalview: remove 2024.1.21 and add 2024.4.2 (new default)
vasp-tpc: deprecate 6.3.2-gpu

## November 13, 2024 ¶

Numerous updates intended to improve system stability: Neo, the file system control software for Perlmutter scratch, was updated to 6.7-022. GPFS updated to 5.1.9.4 efix 23. Update slingshot script to handle switches with recurring issues (>24 flaps in a day). Firmware and hardware updates.
Neo, the file system control software for Perlmutter scratch, was updated to 6.7-022.
GPFS updated to 5.1.9.4 efix 23.
Update slingshot script to handle switches with recurring issues (>24 flaps in a day).
Firmware and hardware updates.
NERSC module updates: amber: remove 20, 20-gpu berkeleygw: deprecate 3.0.1-cpu, 3.0.1-gpu climate-utils: deprecate 2023q2, 2023q2-old codee: remove 2024.2.5, add 2024.3.4 (new default) dmtcp: remove 3.0.0 e4s: remove 23.05 eigen: deprecate 3.4.0 espresso: add 7.3.1-libxc-6.2.2-cpu, 7.3.1-libxc-6.2.2-gpu forge: remove 23.1.2 and 24.0, add 24.0.3 and 24.0.5 (new default) fpm: update to 0.10.1 gromacs: deprecate 2021.5-plumed, 2021.5, 2022.3-gpu intel-llvm: remove 2023-WW13 jamo: update dev, prod, python-jamo to point to new install locations julia: deprecate 1.10.0, 1.10.1, 1.10.2, 1.10.3 math-libs-real32: deprecate 2023q2 mpich: update SLURM_MPI_TYPE in 4.2.2 mumps: deprecate 5.5.1-gcc-11.2.0 mvasp: update all modulefiles based on the latest template; deprecate 5.4.4-cpu namd: deprecate and remove 2.15a2-cpu_mpi, 2.15a2-cpu_ofi, 2.15a2-gpu_ofi nersc_cr: deprecate 23.06 nvidia-mixed: remove 22.2 paraview: add 5.13.0-cpu, 5.13.0-gpu pytorch: remove 1.11.0 spack: remove e4s-23.05, deprecate develop sqs: add 2.0, use script instead of alias (new default) totalview: remove 2023.4.16 valgrind: remove 3.20.0, add 3.23.0 (new default); add a conflict with the valigrind4hpc; fix the suppression path in 3.21.0 and 3.22.0 vasp: update all modulefiles based on the latest template; deprecate 5.4.1-cpu, 6.2.1-gpu, 6.3.2-cpu, 6.3.2-gpu, 6.4.1-cpu, 6.4.1-gpu vasp-tpc: update all modulefiles based on the latest template; deprecate 6.2.1-gpu, 6.3.2-cpu wannier90: deprecate 3.1.0, 3.1.0-gnu, 3.1.0-nvidia
amber: remove 20, 20-gpu
berkeleygw: deprecate 3.0.1-cpu, 3.0.1-gpu
climate-utils: deprecate 2023q2, 2023q2-old
codee: remove 2024.2.5, add 2024.3.4 (new default)
dmtcp: remove 3.0.0
e4s: remove 23.05
eigen: deprecate 3.4.0
espresso: add 7.3.1-libxc-6.2.2-cpu, 7.3.1-libxc-6.2.2-gpu
forge: remove 23.1.2 and 24.0, add 24.0.3 and 24.0.5 (new default)
fpm: update to 0.10.1
gromacs: deprecate 2021.5-plumed, 2021.5, 2022.3-gpu
intel-llvm: remove 2023-WW13
jamo: update dev, prod, python-jamo to point to new install locations
julia: deprecate 1.10.0, 1.10.1, 1.10.2, 1.10.3
math-libs-real32: deprecate 2023q2
mpich: update SLURM_MPI_TYPE in 4.2.2
mumps: deprecate 5.5.1-gcc-11.2.0
mvasp: update all modulefiles based on the latest template; deprecate 5.4.4-cpu
namd: deprecate and remove 2.15a2-cpu_mpi, 2.15a2-cpu_ofi, 2.15a2-gpu_ofi
nersc_cr: deprecate 23.06
nvidia-mixed: remove 22.2
paraview: add 5.13.0-cpu, 5.13.0-gpu
pytorch: remove 1.11.0
spack: remove e4s-23.05, deprecate develop
sqs: add 2.0, use script instead of alias (new default)
totalview: remove 2023.4.16
valgrind: remove 3.20.0, add 3.23.0 (new default); add a conflict with the valigrind4hpc; fix the suppression path in 3.21.0 and 3.22.0
vasp: update all modulefiles based on the latest template; deprecate 5.4.1-cpu, 6.2.1-gpu, 6.3.2-cpu, 6.3.2-gpu, 6.4.1-cpu, 6.4.1-gpu
vasp-tpc: update all modulefiles based on the latest template; deprecate 6.2.1-gpu, 6.3.2-cpu
wannier90: deprecate 3.1.0, 3.1.0-gnu, 3.1.0-nvidia

## November 5, 2024 ¶

Rolling reboot:
Minor version update to 535.216.01 for the GPU driver.
BIOS Firmware updates: GPU nodes updated to 1.5.0. CPU nodes updated to 1.7.5.
GPU nodes updated to 1.5.0.
CPU nodes updated to 1.7.5.

## October 18, 2024 ¶

Podman has been re-enabled everywhere on Perlmutter.
Slingshot upgraded to version 2.2 RC2 and Slingshot Host Software upgraded to 11.0.1 RC2 (with hotfix). This is intended to improve network performance and stability.
Memory limits for individual sessions on the login nodes reduced to 56GB. This is intended to increase login node responsiveness and stability. If you need to run login processes that need more memory, please run on a compute using an interactive job.
Upgraded the GPU driver to 535.183.06.
Darshan added as a default module for all users.
Updated a kernel parameter (rcupdate.rcu_normal_after_boot=1) to avoid a crash for some jobs.
Updating to COS 2.5.147, intended to improve system stability.
Upgrade Slurm to version 23.11.10.
Adding a kernel hotfix from the vendor to correct an upstream bug that caused occasional node crashes.
NERSC module updates: arm-forge: removed, use forge instead berkeleygw: deprecated 3.0.1-cpu, 3.0.1-gpu cmake: added 3.30.2, removed 3.22.0 codee: removed 2024.2.1, 2024.2.3, added 2024.2.5, 2024.3.1 (new default) conda: added Miniforge3-24.7.1-0 darshan: updated 3.4.4 e4s: deprecated 23.05 forge: removed 23.1.1, added 24.0.2 (new default) idl: removed 8.5 mpich: removed 4.2.0, added 4.2.2 openmpi: updated 5.0.3 PrgEnv-llvm: updated 1.0 qchem: added 6.2.0-cpu, 6.2.1-cpu totalview: removed 2023.2.15, added 2024.3.10 (new default) vasp: updated module files for all vasp, vasp-tpc, mvasp; deprecated versions lower than 5.4.4 for 5x and lower than 6.4.2 for 6x
arm-forge: removed, use forge instead
berkeleygw: deprecated 3.0.1-cpu, 3.0.1-gpu
cmake: added 3.30.2, removed 3.22.0
codee: removed 2024.2.1, 2024.2.3, added 2024.2.5, 2024.3.1 (new default)
conda: added Miniforge3-24.7.1-0
darshan: updated 3.4.4
e4s: deprecated 23.05
forge: removed 23.1.1, added 24.0.2 (new default)
idl: removed 8.5
mpich: removed 4.2.0, added 4.2.2
openmpi: updated 5.0.3
PrgEnv-llvm: updated 1.0
qchem: added 6.2.0-cpu, 6.2.1-cpu
totalview: removed 2023.2.15, added 2024.3.10 (new default)
vasp: updated module files for all vasp, vasp-tpc, mvasp; deprecated versions lower than 5.4.4 for 5x and lower than 6.4.2 for 6x

## October 3, 2024 ¶

Podman, NERSC’s new container runtime, has been re-enabled on login nodes. Jobs using containers on compute nodes will still need to use Shifter. Additional documentation on porting between podman-hpc and shifter is available.

## September 23, 2024 ¶

Podman, NERSC’s new container runtime, has been temporarily disabled to address a functionality issue. This affects Apptainer as well. In the meantime, please use Shifter for your container runtimes.

## September 12, 2024 ¶

Neo, the file system control software for Perlmutter scratch, was updated to 6.7-022. This is intended to improve system stabiility.
Fixed issue that was stopping podman-hpc jobs from running via slurm on login nodes.
Firmware and hardware updates. This is intended to improve system stability.

## July 31, 2024 ¶

Maximum job walltime limit increased from 24 to 48 hours.
Upgrade Slurm to version 23.11.
Changed the underlying storage for the Slurm control daemon and its associated database cluster. This is intended to improve performance.
NERSC module updates: berkeleygw: added 4.0-gpu darshan: updated 3.4.4, 3.4.4-cpe-23.03 e4s: removed 22.11 forge: added 24.0 (new default), removed 23.0.2 julia: added 1.10.0, 1.10.1, 1.10.2, 1.10.3, 1.10.4, updated 1.8.5, 1.9.4, removed 1.9.2, 1.9.3 mpich: updated 4.2.0 nvidia: removed 22.2 nvshmem: updated 2.11.0 PrgEnv-llvm: added 1.0 spack: removed e4s-22.11 sqs: updated 1.0 vasp: added 6.4.3-cpu, 6.4.3-gpu, updated 5.4.1-cpu, 5.4.4-cpu, 6.3.2-cpu, 6.4.1-cpu, 6.4.2-cpu, 6.2.1-gpu, 6.3.2-gpu, 6.4.1-gpu, 6.4.2-gpu vasp-tpc: updated 5.4.4-cpu, 6.3.2-cpu, 6.4.2-cpu
berkeleygw: added 4.0-gpu
darshan: updated 3.4.4, 3.4.4-cpe-23.03
e4s: removed 22.11
forge: added 24.0 (new default), removed 23.0.2
julia: added 1.10.0, 1.10.1, 1.10.2, 1.10.3, 1.10.4, updated 1.8.5, 1.9.4, removed 1.9.2, 1.9.3
mpich: updated 4.2.0
nvidia: removed 22.2
nvshmem: updated 2.11.0
PrgEnv-llvm: added 1.0
spack: removed e4s-22.11
sqs: updated 1.0
vasp: added 6.4.3-cpu, 6.4.3-gpu, updated 5.4.1-cpu, 5.4.4-cpu, 6.3.2-cpu, 6.4.1-cpu, 6.4.2-cpu, 6.2.1-gpu, 6.3.2-gpu, 6.4.1-gpu, 6.4.2-gpu
vasp-tpc: updated 5.4.4-cpu, 6.3.2-cpu, 6.4.2-cpu

## June 26, 2024 ¶

Additional 9PB of capacity added to Perlmutter's scratch file system. This capacity will be available to users after testing completes.
Update Slurm configuration to align with changes in hardware discovery.
Hardware and configuration work to prepare for future capacity enhancements.
Hardware and cable replacements. This is intended to increase resiliency.
NERSC module updates: New Features and Improvements: Added cudatoolkit 12.4 Added nvhpc 24.5 Added PyTorch 2.3.1 Added NCCL 2.21.5 Added cuDNN 9.1.0 Added new version of Codee Added Intel 2024.1.0 with NVIDIA GPU support Added OpenMPI 5.0.3 Updates and Changes: Updated PyTorch 2.1.0-cu12 dependencies Updated TensorFlow install locations and modified 2.12 for conda cudatoolkit Moved several cuDNN, NCCL, and PyTorch packages to new paths Changed Spack modulefile to version 0.22 and set as default Deprecations and Removals: Deprecated intel-llvm Removed gpu-test module Removed TensorFlow 2.6 Deprecated E4S 22.11 Deprecated NVIDIA 22.2 Removed cuDNN 8.2.0
New Features and Improvements: Added cudatoolkit 12.4 Added nvhpc 24.5 Added PyTorch 2.3.1 Added NCCL 2.21.5 Added cuDNN 9.1.0 Added new version of Codee Added Intel 2024.1.0 with NVIDIA GPU support Added OpenMPI 5.0.3
Added cudatoolkit 12.4
Added nvhpc 24.5
Added PyTorch 2.3.1
Added NCCL 2.21.5
Added cuDNN 9.1.0
Added new version of Codee
Added Intel 2024.1.0 with NVIDIA GPU support
Added OpenMPI 5.0.3
Updates and Changes: Updated PyTorch 2.1.0-cu12 dependencies Updated TensorFlow install locations and modified 2.12 for conda cudatoolkit Moved several cuDNN, NCCL, and PyTorch packages to new paths Changed Spack modulefile to version 0.22 and set as default
Updated PyTorch 2.1.0-cu12 dependencies
Updated TensorFlow install locations and modified 2.12 for conda cudatoolkit
Moved several cuDNN, NCCL, and PyTorch packages to new paths
Changed Spack modulefile to version 0.22 and set as default
Deprecations and Removals: Deprecated intel-llvm Removed gpu-test module Removed TensorFlow 2.6 Deprecated E4S 22.11 Deprecated NVIDIA 22.2 Removed cuDNN 8.2.0
Deprecated intel-llvm
Removed gpu-test module
Removed TensorFlow 2.6
Deprecated E4S 22.11
Deprecated NVIDIA 22.2
Removed cuDNN 8.2.0

## May 15, 2024 ¶

GPU jobs using at least 128 nodes and CPU jobs using at least 256 nodes now receive a 50% discount.
Purge job data older than 6 months from slurm accounting DB. This is intended to shrink the size of the accounting DB so that slurm can be updated in a future maintnenace.
Increase DVS network credits. This is intended to improve metadata performance.
Adjusted slurm prolog script to avoid start up delays when jobs are submitted from a DVS file system (homes, global common, or CFS).
Modified cooling system settings to improve resiliency and decrease performance variability.
Hardware and cable replacements. This is intended to increase resiliency.
NERSC module updates: codee: default changed from 2023.1.7 to 2024.2.2 darshan: deleted 3.3.1, 3.4.0 kokkos: added 4.3.00 llvm: added 18.1.0 mpich: added 4.2 nsight-compute: deleted 2022.1.1 nsight-system: deleted 2022.1.1 nvshmem: added 2.11 paraview: added 5.12.0, deleted 5.11.1 qchem: added 6.0.0 spack: deleted 0.19.0, 0.19.2 total-view: added 2024.1.21, deleted 2023.1.6, default now 2024.1.21 vasp: added 6.4.2, deprecated 6.2.1, 6.3.2, 5.4.1
codee: default changed from 2023.1.7 to 2024.2.2
darshan: deleted 3.3.1, 3.4.0
kokkos: added 4.3.00
llvm: added 18.1.0
mpich: added 4.2
nsight-compute: deleted 2022.1.1
nsight-system: deleted 2022.1.1
nvshmem: added 2.11
paraview: added 5.12.0, deleted 5.11.1
qchem: added 6.0.0
spack: deleted 0.19.0, 0.19.2
total-view: added 2024.1.21, deleted 2023.1.6, default now 2024.1.21
vasp: added 6.4.2, deprecated 6.2.1, 6.3.2, 5.4.1

## May 1, 2024 ¶

Rolling reboot, login nodes and the scratch file system remained available
Adjusted DVS ksocklnd network driver parameters (credits/peer_credits/conns_per_peer) and returned to default CPU Partitions (CPT). This is intended to improve performance for reads and writes for file systems that use DVS (CFS, homes, and global common).
ksocklnd
Rebuilt slurm with a more recent GCC and deployed with a newer container image. This is intended to increase system stability.

## April 17, 2024 ¶

Changed the DVS service network drivers (from kfilnd to ksocklnd ) to avoid a bug that could cause data corruption. This is expected to reduce performance for large scale I/O by as much as a factor of two.
kfilnd
ksocklnd
Changes to the shifter configuration to allow updates without downtime.
Upgrades to some network configurations to improve stability and better identify components that needed attention.
Chassis controller and node controller firmware updates. This is intended to fix a number of issues including an issue with energy usage reporting on the nodes.
NERSC module updates: darshan: added 3.4.4 and 3.4.4-cpe-23.03 arm-forge / forge: added 23.1.2 as the new default
darshan: added 3.4.4 and 3.4.4-cpe-23.03
arm-forge / forge: added 23.1.2 as the new default

## March 20, 2024 ¶

Slingshot Host Software upgraded to version 2.1.2. This is intended to improve network performance and stability.
NERSC module updates: hip: deleted 5.4.3 libxc: deleted 4.3.4 and 6.2.2 nccl: added 2.19.4 as the new default
hip: deleted 5.4.3
libxc: deleted 4.3.4 and 6.2.2
nccl: added 2.19.4 as the new default
Update to kernel parameters on the DVS nodes. This is intended to improve performance accessing CFS via DVS.
Numerous replacements to address minor hardware issues that occurred since the last maintenance.

## February 22, 2024 ¶

Adjusted network settings to decrease effects of transient network interruptions (aka link flaps).
Update to DVS software to address an issue where nodes were occasionally failing with a “dropped messages” error.
Adjusted GPFS parameters on the gateway nodes to try to improve performance under heavy load.
Added kdreg2 memory registration monitor. Users can test this by setting FI_MR_CACHE_MONITOR=kdreg2 at the beginning of their job.
kdreg2
FI_MR_CACHE_MONITOR=kdreg2
NERSC module updates: codee: default changed from 2023.1.7 to 2024.1.1 forge: default changed from 23.1 to 23.1.1 fpm: added 0.10.0 gsl: deleted 2.7 lammps: deleted 2022.11.03 llvm: deleted 17, nightly updated from v16 to v18 matlab: added R2023b matlab-mcr: added R2023b PrgEnv-llvm: added 0.5 qchem: deleted 5.4.2-cpu and 6.0.0-cpu tensorflow: added 2.15.0 valgrind: added 3.22.0
codee: default changed from 2023.1.7 to 2024.1.1
forge: default changed from 23.1 to 23.1.1
fpm: added 0.10.0
gsl: deleted 2.7
lammps: deleted 2022.11.03
llvm: deleted 17, nightly updated from v16 to v18
matlab: added R2023b
matlab-mcr: added R2023b
PrgEnv-llvm: added 0.5
qchem: deleted 5.4.2-cpu and 6.0.0-cpu
tensorflow: added 2.15.0
valgrind: added 3.22.0

## January 30, 2024 ¶

Rolling reboot:
Podman, NERSC’s new container runtime, re-enabled.
NERSC module updates: pytorch: 1.31.1 and 2.0.1 updated to work with cudatoolkit/11.7 tensorflow: 2.6.0 and 2.12.0 updated to work with cudatoolkit/11.7
pytorch: 1.31.1 and 2.0.1 updated to work with cudatoolkit/11.7
tensorflow: 2.6.0 and 2.12.0 updated to work with cudatoolkit/11.7

## January 17, 2024 ¶

Major changes to user programming environment. We expect most users should not need to re-compile their code, though we recommend testing existing applications in the new environment: CPE upgraded to 23.12 Default cudatoolkit module version updated to cudatoolkit/12.2 gcc compiler will now be provided by the underlying SLES OS Users wishing to access the older programming environment can load the cpe/23.03 module NERSC module updates: openmpi: added 5.0.0 llvm: added 17.0.6, removed 17.0.2 conda: added Miniconda3-py311_23.11.0-2 python: updated environments for compatibility with cpe/23.12
CPE upgraded to 23.12
Default cudatoolkit module version updated to cudatoolkit/12.2
gcc compiler will now be provided by the underlying SLES OS
Users wishing to access the older programming environment can load the cpe/23.03 module
cpe/23.03
NERSC module updates: openmpi: added 5.0.0 llvm: added 17.0.6, removed 17.0.2 conda: added Miniconda3-py311_23.11.0-2 python: updated environments for compatibility with cpe/23.12
openmpi: added 5.0.0
llvm: added 17.0.6, removed 17.0.2
conda: added Miniconda3-py311_23.11.0-2
python: updated environments for compatibility with cpe/23.12
Update BIOS on GPU nodes to address issues where nodes crashed during some jobs with a “DPC Containment” error
Network tuning parameters configured to automatically retune. This is intended to reduce node failures and timeouts during some user jobs.
More details for the above changes can be found in Jan 17, 2024 user announcement email .

## December 20, 2023 ¶

Added 3 PB capacity to the Perlmutter Scratch File System. This increases the total usable capacity to 36 PB.
COS updated to 2.5.143, intended to improve system stability.
Slingshot Host Software upgraded to version 2.1.1. This is intended to improve network performance and stability.
Slurm updated to 23.02.7 and PMIx plugin updated to v4.2.7.
NERSC module updates: forge: add 23.1-linux-x86_64, remove 23.0-linux-x86_64 tensorflow/2.9.0: update XLA_FLAGS to find libdevice totalview: add 2023.4.16, remove 2022.1.11 and 2022.4.27 qchem: add deprecation notice, to be retired Jan 16 2024.
forge: add 23.1-linux-x86_64, remove 23.0-linux-x86_64
tensorflow/2.9.0: update XLA_FLAGS to find libdevice
totalview: add 2023.4.16, remove 2022.1.11 and 2022.4.27
qchem: add deprecation notice, to be retired Jan 16 2024.

## December 14, 2023 ¶

Podman, NERSC’s new container runtime, has been temporarily disabled to address a functionality issue.

## November 29, 2023 ¶

Upgrade to DVS service to improve stability accessing Global Homes, Global Common, and CFS (COS 2.5.139)
Upgrade to Slurm to improve sacct query efficiency
DNA file system mounted read-only on login nodes
Improved experience for Jupyter users during rolling reboots
Removed an upstream issue that could cause node reboots to time out and fail
Numerous replacements to address minor hardware issues that occurred since the last maintenance.
NERSC module updates: cudatoolkit: 11.4 and 11.5 retired, 12.2 added as experimental nvhpc: 21.9 and 21.11 retired, 23.9 added nccl: 2.11.4 retired pytorch: 1.9.0 and 1.10.0 retired, 2.1.0-cu12 added julia: removed many older versions and added many new ones e4s: 23.08 added idl: 8.9 added
cudatoolkit: 11.4 and 11.5 retired, 12.2 added as experimental
nvhpc: 21.9 and 21.11 retired, 23.9 added
nccl: 2.11.4 retired
pytorch: 1.9.0 and 1.10.0 retired, 2.1.0-cu12 added
julia: removed many older versions and added many new ones
e4s: 23.08 added
idl: 8.9 added

## November 17, 2023 ¶

Jobs requesting GPU nodes ( -C gpu ) in the interactive, realtime, and Jupyter QOSes will preferentially run on nodes with twice as much memory (512 GB of RAM and 80 GB of GPU memory per GPU).
-C gpu
Upgrade to Slurm to reduce effects of large numbers of queries.

## November 16, 2023 ¶

Checksums enabled for Perlmutter scratch to protect data integrity from a bug in the underlying Slingshot network driver. This is expected to reduce scratch performance by 17% for large I/O.

## October 10, 2023 ¶

Numerous updates to system software intended to improve stability.
Upgrade Slurm to version 23.02.5.
Fix podman-hpc additionalimagestore bug introduced on September 28.
BIOS update for all GPU nodes. This is intended to improve performance and reliability.
NERSC modules updates: Add gsl/2.7 module to fix an issue with the lammps module. Note this module is deprecated and will be removed on January 16, 2024. We suggest using the GSL library in the directory /usr/lib64 instead. Fix lammps module. Note this module is deprecated and will be removed on January 16, 2024. Fix conda module issue to allow swapping versions of dependent modules. Update NERSC python envs with latest ipympl and matplotlib to be compatible with an upcoming update to NERSC JupyterLab.
Add gsl/2.7 module to fix an issue with the lammps module. Note this module is deprecated and will be removed on January 16, 2024. We suggest using the GSL library in the directory /usr/lib64 instead.
gsl/2.7
lammps
Fix lammps module. Note this module is deprecated and will be removed on January 16, 2024.
lammps
Fix conda module issue to allow swapping versions of dependent modules.
conda
Update NERSC python envs with latest ipympl and matplotlib to be compatible with an upcoming update to NERSC JupyterLab.

## September 28, 2023 ¶

Slingshot Host Software upgraded to version 2.1. This is intended to improve network performance and address issues some codes were seeing at scale.
BIOS updated for all CPU nodes to 1.7.1. This is intended to address performance issues seen by some user codes.
Numerous improvements to NERSC file systems: Gateway nodes configuration changed to optimize DVS thread placement to improve DVS performance for Global Common and CFS. Updated Lustre configuration to further optimize settings for using SSDs (increase trim frequency, changing mb_last_group settings to improve the algorithm looking for free space, and disabling write back throttling).
Gateway nodes configuration changed to optimize DVS thread placement to improve DVS performance for Global Common and CFS.
Updated Lustre configuration to further optimize settings for using SSDs (increase trim frequency, changing mb_last_group settings to improve the algorithm looking for free space, and disabling write back throttling).
mb_last_group
Perlmutter network expanded to allow the ability to deploy increased nodes and file system capacity on demand.
CPE 23.09 deployed as a non-default, experimental environment. To access this, users will need to load the cpe/23.09 module file. We recommend users wishing to use this experimental CPE recompile their codes. Users will also need to manually append -lcudart -lcuda to LDFLAGS when compiling. This is intended to give users early access to new versions of software (including cuda12 with cray-mpich integration). It is not expected that these steps will be necessary when the default CPE is upgraded at a future date.
cpe/23.09
-lcudart -lcuda
Podman-hpc has been upgraded to 1.0.3 to address several issues related to pulling and building. For now users must use podman-hpc images --storage-opt additionalimagestore=$SCRATCH/storage to display migrated images. This is scheduled to be fixed in the next maintenance.
podman-hpc images --storage-opt additionalimagestore=$SCRATCH/storage
Jobs submitted to the preempt QOS for both CPU and GPU architectures must now request a minimum time of 2 hours. Additionally, all jobs submitted to the preempt QOS will now be charged for a minimum of 2 hours of walltime.

## August 23, 2023 ¶

Rolling update to address an issue csh users encountered when accessing modules.

## August 16, 2023 ¶

Numerous improvements to DVS, the I/O forwarding system that delivers CFS and Global Common: Modified DVS scheduling algorithm to use a "fairness" approach so it will serve I/O request more equally across users (previously this was a FIFO like algorithm). This is intended to reduce hangs experienced by all users when a single user overloads a DVS gateway node. Please see our DVS page for best practices for I/O. Optimized DVS monitoring. This is intended to improve stability of the gateway nodes, which are a set of 24 nodes that serve the I/O requests for DVS. Updated the firmware to more optimally communicate over the network ( NPS=1 ). This is intended to improve performance by allowing DVS and GPFS processes to exchange data more efficiently.
Modified DVS scheduling algorithm to use a "fairness" approach so it will serve I/O request more equally across users (previously this was a FIFO like algorithm). This is intended to reduce hangs experienced by all users when a single user overloads a DVS gateway node. Please see our DVS page for best practices for I/O.
Optimized DVS monitoring. This is intended to improve stability of the gateway nodes, which are a set of 24 nodes that serve the I/O requests for DVS.
Updated the firmware to more optimally communicate over the network ( NPS=1 ). This is intended to improve performance by allowing DVS and GPFS processes to exchange data more efficiently.
NPS=1
Neo, the file system control software for Perlmutter scratch, was updated to 6.4-020. This is intended to improve system stabiility.
Shared QOSes for interactive and debug QOS are now availabile. There's also a debug_preempt QOS that can be used for testing preemptive jobs. See our QOSes and Changes page for details.
debug_preempt
The default libfabric memory registration monitor was changed to use userfaultfd instead of memhooks . This is intended to mitigate some intermittent hangs running codes at large scale.
userfaultfd
memhooks
Upgraded Slurm to version 23.02.4. This includes a number of bugfixes intended to increase system stability and functionality as well as a small change to memory usage accounting to more accurately reflect actual usage.
SSH software updated. This is intended to improve system stability.

## August 1, 2023 ¶

Live update:
Extended max timelimit for regular , shared , and overrun QOSes to 24 hours.
regular
shared
overrun

## July 13, 2023 ¶

Reboot, logins remained available (with two brief interruptions)
Updated memory limits on login nodes from 128GiB per user to 64GiB. This is intended to improve login node responsiveness. Please run jobs that require a large amount of memory or cores via the batch system, either in the interactive QOS or as a script.
Updated memory registration monitor to address a problem at scale for NCCL based codes.
Fixed a bug in the shifter gateway that was causing issues with pulling images from registry.nersc.gov
registry.nersc.gov

## June 22, 2023 ¶

Partial rolling reboot:
Updated DVS health monitoring code. This is intended to improve system stability.
Updated Slingshot software to address a bug that was causing nodes to crash.
Mounted the DNA file system read only on all compute nodes. This is intended to improved file system performance.

## June 16, 2023 ¶

Rolling reboot:
Updated DVS health monitoring code. This is intended to improve system stability.
Increased block size for DVS mounts of CFS, Global Common, and Global Homes. This is intended to improve I/O performance.
Added monitoring "heartbeat" functionality. This is intended to improve system monitoring and stability.
Upgraded podman-hpc to version 1.0.2. This is intended to address several bugs identified in early testing.

## June 14, 2023 ¶

Neo, the file system control software for Perlmutter scratch, was rolled back to a custom version based on version 6.3 to avoid a bug that was causing frequent Lustre crashes. This version also included some changes intended to improve performance.

## June 8, 2023 ¶

The Community, Global Common, and Global Homes File Systems moved from native clients to DVS, an HPE proprietary I/O forwarder. This is intended to improve file system stability, reduce hangs when accessing files, and reduce compute node crashes. To facilitate faster load times, Global Common was mounted read-only on the compute nodes. It remains writable on the login nodes.
To facilitate faster load times, Global Common was mounted read-only on the compute nodes. It remains writable on the login nodes.
Neo, the file system control software for Perlmutter scratch, was updated to 6.4-010. This is intended to improve system stabiility.
Updated the Linux OS to address an RDMA bug that was causing Spectrum Scale to crash intermittently on the login nodes.
Updated GPUDirect software that is intended to reduce the number of GPU node crashes.
Updated ulmits to better manage system resources.

## May 25, 2023 ¶

Updated the firmware on network switches. This is intended to address an issue that is causing intermittent failures for large jobs.
The connection between Perlmutter and NGF (the Homes, Common, and Community File Systems) was updated to use publicly routable IP addresses. This is intended to reduce hangs when listing and modifying files on NGF.
Updated the Lustre Network configuration. This is intended to improve file system performance for Perlmutter scratch on the CPU nodes.
Added some bug fixes to slurm to address issues with VNIs in heterogeneous jobs and PMIx functionality.
Performed critical security updates.

## May 18, 2023 ¶

Rolling reboot:
Slurm updated to version 23.02.2. This includes a number of bugfixes intended to increase system stability and functionality.
Shifter configuration updated to address an issue with mounting the homes filesystem.
Slingshot software updated to address an issue with userfaultd memory registration monitor.
userfaultd
Added a bugfix to address an issue where users would occasionally see I/O errors when accessing files on Perlmutter scratch.
Improved network resiliency to login nodes.
Performed cricital security updates.

## May 12, 2023 ¶

Quota enforcement was re-enabled for Perlmutter scratch (see our File Systems Quota and Purging page for details on the Perlmutter scratch quota).

## May 4, 2023 ¶

Updated slurm to allow support for advanced slingshot functionality
Deployed a bugfix designed to reduce the frequency of large MPI jobs failing with an UNDELIVERABLE error
UNDELIVERABLE
Adjusted ssh configuration to fix an issue where users couldn't ssh to compute nodes where they have running jobs
Updated DNS configurations to enable forward and reverse lookups for Perlmutter login and compute nodes from outside the NERSC network. This was intended to address an issue that was greatly slowing ssh connections to some external hosts
Updated DVS version intended to improve performance over DVS
Performed a critical security update for Linux OS
Updated switch configuration to improve security and reliability

## April 27, 2023 ¶

Job submission and running jobs were paused to upgrade slurm to 23.02. This is intended to increase system stability and introduce new batch system functionality.
Neo, the file system control software for Perlmutter scratch, was updated to 6.3-023. This is intended to improve system stabiility.
A reoptimized boot schema was also deployed. This is intended to reduce boot time and improve system stability.
Both the Neo update and boot schema update were applied as a rolling update with jobs running and logins available. Login nodes also remained available for the slurm upgrade.

## April 17, 2023 ¶

Improved the cgroups process control algorithm on the login nodes. This is intended to reduce the rate that user processes have been unexpectedly terminated on the login nodes (this primarily manifested as ssh sessions getting terminated mid-session).
Added experimental DVS mounts of the CFS file system for testing and evaluation.

## April 11, 2023 ¶

Changes to the User Environment: The programming environment has been updated to CPE 23.03. A full list of changes are in the HPE changelog , but notable changes include: Cray MPICH 8.1.25 from 8.1.24 Cray PMI 6.1.10 from 6.1.9 Upgraded the GPU driver to 525.105.17 (open source) Added HPC SDK 23.1. This adds both the nvidia/23.1 and cudatoolkit/12.0 modules. These modules are marked experimental because they are not yet fully integrated with the system MPI so cuda aware MPI will not work with them. Removed HPC SDK 22.5 and 22.9 (nvidia/22.5 and nvidia/22.9 modules). PrgEnv-Intel deployed
The programming environment has been updated to CPE 23.03. A full list of changes are in the HPE changelog , but notable changes include: Cray MPICH 8.1.25 from 8.1.24 Cray PMI 6.1.10 from 6.1.9
Cray MPICH 8.1.25 from 8.1.24
Cray PMI 6.1.10 from 6.1.9
Upgraded the GPU driver to 525.105.17 (open source)
Added HPC SDK 23.1. This adds both the nvidia/23.1 and cudatoolkit/12.0 modules. These modules are marked experimental because they are not yet fully integrated with the system MPI so cuda aware MPI will not work with them.
Removed HPC SDK 22.5 and 22.9 (nvidia/22.5 and nvidia/22.9 modules).
PrgEnv-Intel deployed
Batch System Changes: Shared QOS enabled for GPU nodes Slurm has been changed to prevent accidental cancellation of scrontab jobs which would lead to the entire scrontab entry being disabled.
Shared QOS enabled for GPU nodes
Slurm has been changed to prevent accidental cancellation of scrontab jobs which would lead to the entire scrontab entry being disabled.
Changes to address file system stability and performance: Switched to fair queueing to address connection timeouts with the NGF file system and increased max receiver threads. These are intended to address stability issues with CFS. Optimized routing between login nodes and NGF servers. This is intended to reduce pauses when accessing, creating, or updating files on CFS, global common, and homes. Updated Neo, the file system control software for Perlmutter scratch, to 6.3-022. This is intended to increase file system stability and performance.
Switched to fair queueing to address connection timeouts with the NGF file system and increased max receiver threads. These are intended to address stability issues with CFS.
Optimized routing between login nodes and NGF servers. This is intended to reduce pauses when accessing, creating, or updating files on CFS, global common, and homes.
Updated Neo, the file system control software for Perlmutter scratch, to 6.3-022. This is intended to increase file system stability and performance.
Numerous changes intended to improve system resiliency and stability Retooled the internal boot logic to dramatically reduce time for node reboots. In addition to shortening maintenance times, this lays the groundwork for improved health checks to more efficiently remove problem nodes from the batch system. Mapped power paths to critical infrastructure. No changes were made, but this involved physically interacting with the cables and plugs so it was done during maintenance to avoid disruption. This is intended to increase system resiliency and stability.
Retooled the internal boot logic to dramatically reduce time for node reboots. In addition to shortening maintenance times, this lays the groundwork for improved health checks to more efficiently remove problem nodes from the batch system.
Mapped power paths to critical infrastructure. No changes were made, but this involved physically interacting with the cables and plugs so it was done during maintenance to avoid disruption. This is intended to increase system resiliency and stability.

## March 20, 2023 ¶

The SS11 feature for performant GPU-RDMA has been re-enabled for all new jobs starting as of 9:30am PDT. NERSC worked with the vendors to obtain a workaround for the issue and deployed it this morning on the compute nodes using a non-disruptive rolling reboot. We expect to deploy a full fix during the next scheduled maintenance on March 22, 2023.

## March 15, 2023 ¶

A SS11 feature for performant GPU-RDMA has been temporarily disabled to mitigate a critical issue leading to node failures. This is expected to substantially affect performance of applications using GPU-RDMA capabilities for inter-node communication (such as CUDA-Aware MPI or GASNet), but will allow jobs that were previously crashing to run. We expect to be able to remove this mitigation during the next scheduled maintenance on March 22, 2023. This mitigation was removed on March 20, 2023 .

## March 8, 2023 ¶

The programming environment has been updated to CPE 23.02. A full list of changes are in the HPE changelog , but notable changes include: Cray MPICH 8.1.24 from 8.1.22 Cray PMI 6.1.9 from 6.1.7 HDF5 1.12.2.3 from 1.12.2.1 Parallel NetCDF 1.12.3.3 from 1.12.3.1
Cray MPICH 8.1.24 from 8.1.22
Cray PMI 6.1.9 from 6.1.7
HDF5 1.12.2.3 from 1.12.2.1
Parallel NetCDF 1.12.3.3 from 1.12.3.1
Moved to using the open NVIDIA driver instead of the proprietary driver (keeping the version the same at 515.65.01) to include new functionality that will enable sharing GPU nodes.
Moving the gateway nodes (nodes used for communication with external resources like NGF) to the “stock” SLES kernel to be able to leverage the kernel fastpath feature for packet forwarding. This is intended to improve read and write rates to NGF file systems.
General software and cabling updates to increase system stability and performance. Recable the internal network to minimize the impact of a switch failure on the high-speed network. By ensuring that the fabric manager (the software that controls Perlmutter’s interior network) maintains connectivity to each high-speed network group, this will provide additional resiliency system-wide. Upgrade the Slingshot software to add improvements in the retry handler algorithm (this governs how missed packets are handled) to reduce amplification of messages about inaccessible nodes and to fix a bug that caused certain user codes to crash. This is intended to increase network and compute resiliency. Update the COS software (a software layer that contains the underlying SLES OS as well as interfaces to other things like the file system) to upstream a SLES fix to address a readahead issue that was crashing nodes. This is intended to improve system stability. Updated Neo, the file system control software, to 6.2-015. This is intended to increase file system stability and performance.
Recable the internal network to minimize the impact of a switch failure on the high-speed network. By ensuring that the fabric manager (the software that controls Perlmutter’s interior network) maintains connectivity to each high-speed network group, this will provide additional resiliency system-wide.
Upgrade the Slingshot software to add improvements in the retry handler algorithm (this governs how missed packets are handled) to reduce amplification of messages about inaccessible nodes and to fix a bug that caused certain user codes to crash. This is intended to increase network and compute resiliency.
Update the COS software (a software layer that contains the underlying SLES OS as well as interfaces to other things like the file system) to upstream a SLES fix to address a readahead issue that was crashing nodes. This is intended to improve system stability.
readahead
Updated Neo, the file system control software, to 6.2-015. This is intended to increase file system stability and performance.

## February 23, 2023 ¶

Numerous changes intended to improve network stability and file system access Further changes to the TCP queue discipline to more fairly allocate bandwidth on our gateway nodes (nodes used for communication with external resources like NGF) between all the TCP streams from the computes while keeping latencies at optimal levels. This is intended to improve access to file systems like CFS, global common and global homes for batch jobs. Connected gateway nodes to new switches. This is intended to improve network performance and resiliency. Multiple cable adjustments to bring system into compliance with its cabling plan. This is intended to simplify maintenance and improve resiliency.
Further changes to the TCP queue discipline to more fairly allocate bandwidth on our gateway nodes (nodes used for communication with external resources like NGF) between all the TCP streams from the computes while keeping latencies at optimal levels. This is intended to improve access to file systems like CFS, global common and global homes for batch jobs.
Connected gateway nodes to new switches. This is intended to improve network performance and resiliency.
Multiple cable adjustments to bring system into compliance with its cabling plan. This is intended to simplify maintenance and improve resiliency.

## February 19, 2023 ¶

Multi-connection over TCP set back to 1 (from 2) for CFS to mitigate a bug.

## February 15, 2023 ¶

Numerous changes intended to improve network stability and file system access. General Network Issues: Added static ARP entries for the compute nodes. This is intended to fix the issue where a large number of jobs either failed to launch or started in slurm but produce no output. Increased sweep frequency for the fabric manager, the software that controls Perlmutter’s interior network, and added shorter timeouts throughout the system. These changes are intended to improve general network robustness and shorten recovery times for component failures. Replaced a defective network switch. Added code to filter bad unicast traffic from the network. This is intended to improve network stability. Filesystem hangs and slowness: Adjusted port policy for Lustre file system and debugged long recovery times for single component failure in Lustre. This is intended to inform and simplify future work to improve Lustre reliability and responsiveness.
General Network Issues: Added static ARP entries for the compute nodes. This is intended to fix the issue where a large number of jobs either failed to launch or started in slurm but produce no output. Increased sweep frequency for the fabric manager, the software that controls Perlmutter’s interior network, and added shorter timeouts throughout the system. These changes are intended to improve general network robustness and shorten recovery times for component failures. Replaced a defective network switch. Added code to filter bad unicast traffic from the network. This is intended to improve network stability.
Added static ARP entries for the compute nodes. This is intended to fix the issue where a large number of jobs either failed to launch or started in slurm but produce no output.
Increased sweep frequency for the fabric manager, the software that controls Perlmutter’s interior network, and added shorter timeouts throughout the system. These changes are intended to improve general network robustness and shorten recovery times for component failures.
Replaced a defective network switch.
Added code to filter bad unicast traffic from the network. This is intended to improve network stability.
Filesystem hangs and slowness: Adjusted port policy for Lustre file system and debugged long recovery times for single component failure in Lustre. This is intended to inform and simplify future work to improve Lustre reliability and responsiveness.
Adjusted port policy for Lustre file system and debugged long recovery times for single component failure in Lustre. This is intended to inform and simplify future work to improve Lustre reliability and responsiveness.

## February 9, 2023 ¶

Numerous changes intended to improve network stability and file system access. General Network Issues: Change default TCP queue discipline to fq_codel to address missing patch in SLES 15SP4. This is intended to address many of the communication failures larger scale jobs are experiencing. Recabling (replacing defective equipment and correcting misconnected cables). This is a lengthly physical process and is intended to increase network stability. Updating firmware to improve network link stability and reliability of key I/O nodes. Filesystem hangs, slowness, and I/O errors: Numerous network tuning and changes (Increase Multi-connection over TCP to 2 to maximize connectivity to Spectrum Scale servers, ipoib parameter changes, etc.). This is intended to reduce stale file handles and job failures from nodes getting expelled from the Spectrum Scale cluster. Components that use DVS (an I/O forwarding service within Perlmutter) have been converted to using other delivery methods. This is intended to reduce the number of software components in use in order to simplify debugging of the network issues. Most users will not be affected by this change. Users using read-only mounts of CFS may see slower or more-variable performance while the system is in this configuration. cvmfs is now delivered using native clients and loop mounted file systems for caching following the recommended HPC recipe .
General Network Issues: Change default TCP queue discipline to fq_codel to address missing patch in SLES 15SP4. This is intended to address many of the communication failures larger scale jobs are experiencing. Recabling (replacing defective equipment and correcting misconnected cables). This is a lengthly physical process and is intended to increase network stability. Updating firmware to improve network link stability and reliability of key I/O nodes.
Change default TCP queue discipline to fq_codel to address missing patch in SLES 15SP4. This is intended to address many of the communication failures larger scale jobs are experiencing.
fq_codel
Recabling (replacing defective equipment and correcting misconnected cables). This is a lengthly physical process and is intended to increase network stability.
Updating firmware to improve network link stability and reliability of key I/O nodes.
Filesystem hangs, slowness, and I/O errors: Numerous network tuning and changes (Increase Multi-connection over TCP to 2 to maximize connectivity to Spectrum Scale servers, ipoib parameter changes, etc.). This is intended to reduce stale file handles and job failures from nodes getting expelled from the Spectrum Scale cluster. Components that use DVS (an I/O forwarding service within Perlmutter) have been converted to using other delivery methods. This is intended to reduce the number of software components in use in order to simplify debugging of the network issues. Most users will not be affected by this change. Users using read-only mounts of CFS may see slower or more-variable performance while the system is in this configuration. cvmfs is now delivered using native clients and loop mounted file systems for caching following the recommended HPC recipe .
Numerous network tuning and changes (Increase Multi-connection over TCP to 2 to maximize connectivity to Spectrum Scale servers, ipoib parameter changes, etc.). This is intended to reduce stale file handles and job failures from nodes getting expelled from the Spectrum Scale cluster.
Components that use DVS (an I/O forwarding service within Perlmutter) have been converted to using other delivery methods. This is intended to reduce the number of software components in use in order to simplify debugging of the network issues. Most users will not be affected by this change. Users using read-only mounts of CFS may see slower or more-variable performance while the system is in this configuration. cvmfs is now delivered using native clients and loop mounted file systems for caching following the recommended HPC recipe .
Users using read-only mounts of CFS may see slower or more-variable performance while the system is in this configuration.
cvmfs is now delivered using native clients and loop mounted file systems for caching following the recommended HPC recipe .
Podman deployed on the system.

## February 1, 2023 ¶

Network updates intended to improve stability. This maintenance was appended to the unscheduled outage to minimize disruption to users. Automatically reboot compute nodes that are in a particular fail mode (softlockup). These nodes cause instability in our Spectrum Scale file systems (CFS, homes, and global common) and rebooting them is intended to reduce file system hangs and outages. Changed protocol for communication to the Spectrum Scale cluster to RDMA on Perlmutter login nodes. This is intended to reduce issues accessing the file system.
Automatically reboot compute nodes that are in a particular fail mode (softlockup). These nodes cause instability in our Spectrum Scale file systems (CFS, homes, and global common) and rebooting them is intended to reduce file system hangs and outages.
Changed protocol for communication to the Spectrum Scale cluster to RDMA on Perlmutter login nodes. This is intended to reduce issues accessing the file system.

## January 25, 2023 ¶

Updates intended to improve network stability and access of cvmfs.

## January 19, 2023 ¶

Network update intended to improve stability and address Lustre performance issues.
Preemptible jobs on Perlmutter are free until February 19, 2023.
Darshan module removed from list of default modules loaded at start up.

## December 21, 2022 ¶

Major hardware issues that were impacting the network performance have been addressed and PM has undergone massive full scale stress testing
The Slingshot software stack has been updated to a new version that is expected to be more robust.
256 GPUs nodes with double the GPU-attached memory have been added to the system. Please see our jobs policy page for instructions on how to access them.
1536 new CPU nodes have been added to the system.
A new NVIDIA NCCL plugin has been installed that more efficiently uses the Slingshot network. This has been integrated into NERSC’s machine learning and vasp modules so if you use these modules no further action is needed. However, other workflows will need some adjusting: You will now need to use the --module=nccl-2.15 to get access to the new nccl plugin in shifter. Please see our shifter documentation for instructions. If you install your own software that depends on NCCL, please use the new nccl module to get access to the new NCCL plugin libraries Some machine learning workloads running in older NGC containers (versions from before 2022) may encounter performance variability. These issues can be fixed by upgrading the container to a more recent version.
You will now need to use the --module=nccl-2.15 to get access to the new nccl plugin in shifter. Please see our shifter documentation for instructions.
--module=nccl-2.15
If you install your own software that depends on NCCL, please use the new nccl module to get access to the new NCCL plugin libraries
nccl
Some machine learning workloads running in older NGC containers (versions from before 2022) may encounter performance variability. These issues can be fixed by upgrading the container to a more recent version.
The OS has been updated to SLES SP4 and the programming environment has been updated to CPE 22.11. Due to changes in the SLES SP4 system libraries, changes may be required for conda environments built or invoked without using the NERSC provided python module. Users may see errors like ImportError: /usr/lib64/libssh.so.4: undefined symbol: EVP_KDF_CTX_new_id, version OPENSSL_1_1_1d . Please see our Perlmutter python documentation for more information. The default version of the NVIDIA HPC SDK compiler was upgraded to 22.7 (from 22.5) Cray MPICH upgraded to 8.1.22 (from 8.1.17) GCC v12 now available
Due to changes in the SLES SP4 system libraries, changes may be required for conda environments built or invoked without using the NERSC provided python module. Users may see errors like ImportError: /usr/lib64/libssh.so.4: undefined symbol: EVP_KDF_CTX_new_id, version OPENSSL_1_1_1d . Please see our Perlmutter python documentation for more information.
python
ImportError: /usr/lib64/libssh.so.4: undefined symbol: EVP_KDF_CTX_new_id, version OPENSSL_1_1_1d
The default version of the NVIDIA HPC SDK compiler was upgraded to 22.7 (from 22.5)
Cray MPICH upgraded to 8.1.22 (from 8.1.17)
GCC v12 now available

## October 28, 2022 ¶

Charging for all jobs began.

## October 26, 2022 ¶

Slurm updated to 22.05
The 128-node limit on the regular QOS for GPU nodes has been removed. Regular can now accept jobs of all sizes.
regular
The early_science QOS has been removed. Please use regular instead. All queued jobs in the early_science QOS have been moved to regular .
early_science
regular
early_science
regular
Numerous updates intended to improve system stability and networking

## October 11, 2022 ¶

Major changes to the internal network and file system to get Perlmutter into its final configuration. Some tuning and changes are still required and will be applied over the next few weeks

## September 15, 2022 ¶

Perlmutter scratch is now available, but it is still undergoing physical maintenance. We expect scratch performance to be degraded and single-component failures could cause the filesystem to become unavailable during this physical maintenance. We estimate a 20% chance that this will occur in the next month. Please hold any jobs with scratch licenses that you don't want to run by noon on Friday (9/16) with scontrol hold <jobid> .
scontrol hold <jobid>
Numerous updates intended to improve system stability and Community and Home File System access.

## September 7, 2022 ¶

The software environment has been retooled to better focus on GPU usage. These changes should be transparent to the vast majority of both GPU and CPU codes and will help remove the toil of reloading the same modules for every script for GPU-based codes. As our experience with the system grows, we expect to be adding more settings that are expected to be globally beneficial. New gpu module added as a default module loaded at login. It includes: module load cudatoolkit module load load craype-accel-nvidia80 Sets MPICH_GPU_SUPPORT_ENABLED=1 to enable access to CUDA-aware Cray MPICH at runtime A companion cpu module This module is mutually exclusive to the gpu module; if one is loaded, the other will be unloaded In the future we may add any modules or environment settings we find to be generally beneficial to CPU codes, but for now it is empty Given the current contents, CPU users should be able to run their codes with the gpu module. But if there are any problems, users can module load cpu to revert the gpu module Shifter users who want CUDA-aware Cray MPICH at runtime will need to use the cuda-mpich shifter module
New gpu module added as a default module loaded at login. It includes: module load cudatoolkit module load load craype-accel-nvidia80 Sets MPICH_GPU_SUPPORT_ENABLED=1 to enable access to CUDA-aware Cray MPICH at runtime
gpu
module load cudatoolkit
module load cudatoolkit
module load load craype-accel-nvidia80
module load load craype-accel-nvidia80
Sets MPICH_GPU_SUPPORT_ENABLED=1 to enable access to CUDA-aware Cray MPICH at runtime
MPICH_GPU_SUPPORT_ENABLED=1
A companion cpu module This module is mutually exclusive to the gpu module; if one is loaded, the other will be unloaded In the future we may add any modules or environment settings we find to be generally beneficial to CPU codes, but for now it is empty Given the current contents, CPU users should be able to run their codes with the gpu module. But if there are any problems, users can module load cpu to revert the gpu module
cpu
This module is mutually exclusive to the gpu module; if one is loaded, the other will be unloaded
gpu
In the future we may add any modules or environment settings we find to be generally beneficial to CPU codes, but for now it is empty
Given the current contents, CPU users should be able to run their codes with the gpu module. But if there are any problems, users can module load cpu to revert the gpu module
gpu
module load cpu
gpu
Shifter users who want CUDA-aware Cray MPICH at runtime will need to use the cuda-mpich shifter module
Long-lived scrontab capabilities added to better support workflows
A number of performance counters (e.g., CPU, Memory) that are used by NERSC supported performance profiling tools have been re-enabled on the system

## August 24, 2022 ¶

Perlmutter Scratch file system unmounted for upgrading. All data on Perlmutter Scratch will be unavailable. Jobs already in the queue that were submitted from Perlmutter Scratch will be automatically held. If you submitted a job that depends on scratch from another file system, you can add a scratch license with scontrol update job=<job id> Licenses=scratch[,<other existing licenses>...] to have your job held until scratch is available.
scontrol update job=<job id> Licenses=scratch[,<other existing licenses>...]
Numerous internal updates to the software and network for the Phase-2 integration of Perlmutter.

## August 15, 2022 ¶

All Slingshot10 GPU nodes are removed from the system along with their corresponding QOSes (e.g., regular_ss10 ) Any queued jobs in the Slingshot10 QOSes were moved to their corresponding Slingshot11 QOSes
regular_ss10
Any queued jobs in the Slingshot10 QOSes were moved to their corresponding Slingshot11 QOSes
Numerous internal updates to the software and network for the Phase-2 integration of Perlmutter.

## August 8, 2022 ¶

Added NVIDIA HPC SDK Version 22.7 To use: module load PrgEnv-nvidia nvidia/22.7
To use: module load PrgEnv-nvidia nvidia/22.7
module load PrgEnv-nvidia nvidia/22.7
Numerous internal updates to the software and network for the Phase-2 integration of Perlmutter.

## August 1, 2022 ¶

Default switched to Slingshot11 for GPU nodes. Default QOS switched from GPU nodes using the Slingshot10 interconnect to nodes using the Slingshot11 interconnect. If you still wish to run on the Slingshot10 GPU nodes, you can add _ss10 to the QOS on your job submission line (e.g., -q regular_ss10 -C gpu ). All queued jobs will run in the QOS that was active when they were submitted. Use squeue --me -O JobID,Name,QOS,Partition to check which QOS and partition your jobs are in. Login nodes now use the Slingshot11 interconnect.
Default QOS switched from GPU nodes using the Slingshot10 interconnect to nodes using the Slingshot11 interconnect. If you still wish to run on the Slingshot10 GPU nodes, you can add _ss10 to the QOS on your job submission line (e.g., -q regular_ss10 -C gpu ). All queued jobs will run in the QOS that was active when they were submitted.
_ss10
-q regular_ss10 -C gpu
Use squeue --me -O JobID,Name,QOS,Partition to check which QOS and partition your jobs are in.
squeue --me -O JobID,Name,QOS,Partition
Login nodes now use the Slingshot11 interconnect.
CUDA driver upgraded to version 515.48.07
NVIDIA HPC SDK ( PrgEnv-nvidia ) and CUDA Toolkit ( cudatoolkit ) module defaults upgraded to 22.5 and 11.7 respectively. The previous versions are still available. CUDA compatibility libraries are no longer needed, so if you were employing work arounds to remove them they should no longer be needed.
PrgEnv-nvidia
cudatoolkit
CUDA compatibility libraries are no longer needed, so if you were employing work arounds to remove them they should no longer be needed.
Numerous internal updates to the software and network for the Phase-2 integration of Perlmutter.

## June 20, 2022 ¶

Default striping of all user scratch directories set to stripe across a single OST because of a bug in the Progressive File Layout striping schema. If you are reading or writing files larger than 1GB please see our recommendations for Lustre file striping .

## July 18, 2022 ¶

The second set of GPU nodes have been upgraded to Slingshot11 and added to the regular_ss11 QOS (see the discussion in July 11, 2022). We expect the number of Slingshot11 GPU nodes to be changing over the next few weeks, so we recommend you use sinfo to track the number of nodes in each partition. You can use sinfo --format="%.15b %.8D" for concise summary of nodes or sinfo -o "%.20P %.5a %.10D %.16F" for more verbose output.
regular_ss11
We expect the number of Slingshot11 GPU nodes to be changing over the next few weeks, so we recommend you use sinfo to track the number of nodes in each partition. You can use sinfo --format="%.15b %.8D" for concise summary of nodes or sinfo -o "%.20P %.5a %.10D %.16F" for more verbose output.
sinfo
sinfo --format="%.15b %.8D"
sinfo -o "%.20P %.5a %.10D %.16F"

## July 11, 2022 ¶

First GPU nodes are upgraded to use the Slingshot11 interconnect. These nodes have upgraded software and 4x25GB/s NICs (previously they had 2x12.5GB/s NICs). Jobs will need to explicitly request these nodes by adding _ss11 to the QOS, eg -C gpu -q regular_ss11 . There are currently 256 nodes converted to Slingshot11. We expect this number of nodes to be changing over the next few weeks, so we recommend you use sinfo to track the number of nodes in each partition. You can use sinfo --format="%.15b %.8D" for concise summary of nodes or sinfo -o "%.20P %.5a %.10D %.16F" for more verbose output.
_ss11
-C gpu -q regular_ss11
There are currently 256 nodes converted to Slingshot11. We expect this number of nodes to be changing over the next few weeks, so we recommend you use sinfo to track the number of nodes in each partition. You can use sinfo --format="%.15b %.8D" for concise summary of nodes or sinfo -o "%.20P %.5a %.10D %.16F" for more verbose output.
sinfo
sinfo --format="%.15b %.8D"
sinfo -o "%.20P %.5a %.10D %.16F"
CPE default updated to 22.06. Notable changes: PrgEnv-cray (cce/14) now supports OpenMP offload and OpenACC on Perlmutter GPUs cray mpich upgraded to 8.1.17 (from 8.1.15)
PrgEnv-cray (cce/14) now supports OpenMP offload and OpenACC on Perlmutter GPUs
cray mpich upgraded to 8.1.17 (from 8.1.15)
NVIDIA compiler version 22.5 and cudatoolkit SDK version 11.7 now available on the system. These will become the defaults soon.
Shared QOS now available on the CPU nodes
Numerous internal updates to the software and network to prepare the Phase-2 integration of Perlmutter and make cvmfs more stable

## June 6, 2022 ¶

Changes to the batch system Users can now use just -A <account name> (i.e., the extra _g is no longer needed) for jobs requesting GPU resources. Xfer QOS added for data transfers Debug QOS now the default
Users can now use just -A <account name> (i.e., the extra _g is no longer needed) for jobs requesting GPU resources.
-A <account name>
_g
Xfer QOS added for data transfers
Debug QOS now the default
The cuda compatibility libraries were removed from the PrgEnv-nvidia module (specifically the nvidia module). The cuda compatibility libraries are now exclusively in the cudatoolkit module and users are reminded to load this module if they are compiling code for the GPUs.
nvidia
cudatoolkit
Second set of CPU nodes are now available to users.
Numerous internal updates to the software and network to prepare the Phase-2 integration of Perlmutter

## June, 2022 ¶

Achieving 70.9 Pflop/s (FP64 Tensor Core) using 1,520 compute nodes, Perlmutter is ranked 7 th in the Top500 list .

## May 25, 2022 ¶

Maximum job walltime for regular (CPU and GPU nodes) and early_science (GPU nodes) QOSes increased to 12 hours
regular
early_science

## May 17, 2022 ¶

Perlmutter opened to all NERSC Users!
The default Programming Environment is changed to PrgEnv-gnu
Shifter MPI now working on CPU nodes
PrgEnv-aocc now working
Numerous internal updates to the software and network to prepare the Phase-2 integration of Perlmutter

## May 11, 2022 ¶

The first set of Slingshot11 CPU nodes are now available for user jobs. Please see the Perlmutter QOS policy page for QOS details.

## April 29, 2022 ¶

CPE default updated to 22.04. You may choose to load an older CPE but the behavior is not guaranteed. Notable changes — cray mpich upgraded to 8.1.15
Notable changes — cray mpich upgraded to 8.1.15
Nvidia driver has been updated to 470.103.01
Removed nvidia/21.9 (nvhpc sdk 21.9) from the system cudatoolkit/11.0 and cudatoolkit/11.4 dropped as available modules. You can continue to compile using older cuda versions with CUDA compatibility libraries
nvidia/21.9
cudatoolkit/11.0 and cudatoolkit/11.4 dropped as available modules.
cudatoolkit/11.0
cudatoolkit/11.4
You can continue to compile using older cuda versions with CUDA compatibility libraries
Numerous internal upgrades (software and network stack) to prepare the Phase-2 integration of Perlmutter Re-compile is not needed, but if you’re having issues please do try recompiling your application first.
Re-compile is not needed, but if you’re having issues please do try recompiling your application first.

## April 21, 2022 ¶

Node limit restriction for early_science qos has been lifted. Perlmutter QOS policy.
early_science

## April 7, 2022 ¶

NVIDIA Data Center GPU Manager (dcgm) enabled on all nodes. Users will need to disable dcgm before running profiler tools that require access to hardware counters .
Newest versions (2022.x) of nsight-compute and nsight-system removed pending vendor bug fixes
Numerous internal updates to improvement configuration, reliability, and performance

## March 25, 2022 ¶

Numerous internal updates to improvement configuration, reliability, and performance

## March 10, 2022 ¶

Nvidia HPC SDK v21.11 now default
Older cudatoolkit modules removed
Slurm upgrade to 21.08, codes that use gpu-binding will need to be reworked
CPE 21.11 has been retired There will be no support for gcc/9.3 nvcc v11.0 ( cudatoolkit/11.0 ) retired, will no longer be supported
There will be no support for gcc/9.3
gcc/9.3
nvcc v11.0 ( cudatoolkit/11.0 ) retired, will no longer be supported
cudatoolkit/11.0
Numerous internal updates to improvement configuration, reliability, and performance

## February 24, 2022 ¶

Cudatoolkit modules simplified New modules with shorter names point to the most recent releases available Old modules will remain on the system for a short time to allow time to switch over
New modules with shorter names point to the most recent releases available
Old modules will remain on the system for a short time to allow time to switch over
Nvidia HPC SDK v21.11 now available Default will remain 21.9 for a short time to allow time for testing nvidia/21.9 does not support Milan, so the Cray compiler wrappers will build for Rome instead. We recommend that users switch to nvidia/22.11 .
Default will remain 21.9 for a short time to allow time for testing
nvidia/21.9 does not support Milan, so the Cray compiler wrappers will build for Rome instead. We recommend that users switch to nvidia/22.11 .
nvidia/21.9
nvidia/22.11
Upgraded to CPE 22.02. Major changes include: MPICH 8.1.12 to 8.1.13 PMI 6.0.15 to 6.0.17 hdf5 1.12.0.7 to 1.12.1.1 netcdf 4.7.4 to 4.8.1.1
MPICH 8.1.12 to 8.1.13
PMI 6.0.15 to 6.0.17
hdf5 1.12.0.7 to 1.12.1.1
netcdf 4.7.4 to 4.8.1.1
Change to sshproxy to support broader kinds of logins
Realtime qos functionality added
Numerous internal updates to improvement configuration, reliability, and performance

## February 10, 2022 ¶

Node limit for all jobs temporarily lowered to 128 nodes
QOS priority modified to encourage wider job variety

## January 25, 2022 ¶

Cudatoolkit modules now link to correct math libraries (fixes Known Issue "Users will encounter problems linking CUDA math libraries").
Update to DVS configuration to support CVMFS.
The latest Nsight systems and Nsight compute performance tools are now available.
Numerous internal upgrades to improve configuration and performance.

## January 11, 2022 ¶

Upgraded to CPE 21.12. Major changes include: MPICH upgraded to v8.1.12 (from 8.1.11)
MPICH upgraded to v8.1.12 (from 8.1.11)
The previous programming environment can now be accessed using the cpe module .
cpe
Numerous internal upgrades to improve configuration and performance.

## December 21, 2021 ¶

GPUs are back in "Default" mode (fixes Known Issue "GPUs are in "Exclusive_Process" instead of "Default" mode")
User access to hardware counters restored (fixes Known Issue "Nsight Compute or any performance profiling tool requesting access to h/w counters will not work")
Cuda 11.5 compatibility libraries installed and incorporated into Shifter
QOS priority modified to encourage wider job variety
Numerous internal upgrades

## December 6, 2021 ¶

Major changes to the user environment. All users should recompile their code following our compile instructions
The cuda , cray-pmi , and cray-pmi-lib modules have been removed from the default environment
cuda
cray-pmi
cray-pmi-lib
The darshan v3.3.1 module has been added to the default environment
darshan
Default NVIDIA compiler upgraded to v21.9 Users must load a cudatoolkit module to compile GPU codes
Users must load a cudatoolkit module to compile GPU codes
cudatoolkit
Upgraded to CPE 21.11 MPICH upgraded to v8.1.11 (from 8.1.10) PMI upgraded to v6.0.16 (from 6.0.14) FFTW upgraded to 3.3.8.12 (from 3.3.8.11) Python upgraded to 3.9 (from 3.8)
MPICH upgraded to v8.1.11 (from 8.1.10)
PMI upgraded to v6.0.16 (from 6.0.14)
FFTW upgraded to 3.3.8.12 (from 3.3.8.11)
Python upgraded to 3.9 (from 3.8)
Upgrade to SLES15sp2 OS
Numerous internal upgrades

## November 30, 2021 ¶

Upgraded Slingshot (internal high speed network) to v1.6
Upgraded Lustre server
Internal configuration upgrades

## November 16, 2021 ¶

This was a rolling update where the whole system was updated with minimal interruptions to users.
Set MPICH_ALLGATHERV_PIPELINE_MSG_SIZE=0 to improve MPI communication speed for large buffer size.
MPICH_ALLGATHERV_PIPELINE_MSG_SIZE=0
Added gpu and cuda-mpich Shifter modules to better support Shifter GPU jobs
gpu
cuda-mpich
Deployed fix for CUDA Unknown Error errors that occasionally happen for Shifter jobs using the GPUs
CUDA Unknown Error
Changed ssh settings to reduce frequency of dropped ssh connections
Internal configuration updates

## November, 2021 ¶

Perlmutter achieved 70.9 Pflop/s (FP64 Tensor Core) using 1,520 compute nodes, putting the system at No. 5 in the Top500 list .

## November 2, 2021 ¶

Updated to CPE 21.10. A recompile is recommended but not required. See the documentation of CPE changes from HPE for a full list of changes. Major changes of note include: Upgrade MPICH to 8.1.10 (from 8.1.9) Upgrade DSMML to 0.2.2 (from 0.2.1) Upgraded PMI to 6.0.14 (from 6.0.13)
Upgrade MPICH to 8.1.10 (from 8.1.9)
Upgrade DSMML to 0.2.2 (from 0.2.1)
Upgraded PMI to 6.0.14 (from 6.0.13)
Adjusted QOS configurations to facilitate Jupyter notebook job scheduling.
Added preempt QOS. Jobs submitted to this QOS may get preempted after two hours, but may start more quickly. Please see our instructions for running preemptible jobs for details.
preempt

## October 20, 2021 ¶

External ssh access enabled for Perlmutter login nodes.

## October 18, 2021 ¶

Updated slurm job priorities to more efficiently utilize the system and improve the diversity of running jobs.

## October 14, 2021 ¶

Updated NVIDIA driver (to 450.162). This is not expected to have any user impact.
Upgraded internal management framework.

## October 9, 2021 ¶

Screen and tmux installed
Screen
tmux
Installed boost v1.66
Upgraded nv_peer_mem driver to 1.2 (not expected to have any user impact)

## October 5, 2021 ¶

Deployed sparewarmer QOS to assist with node-level testing. This is not expected to have any user impact.
sparewarmer

## October 4, 2021 ¶

Limited the wall time of batch jobs to 6 hours to allow a variety of jobs to run during testing. If you need to run jobs for longer than 6 hours, please open a ticket .

## September 29, 2021 ¶

Numerous internal network and management upgrades.

## New batch system structure deployed ¶

Users will need to specify a QOS (with -q regular , debug , interactive , etc.) as well as a project GPU allocation account name which ends in _g (e.g., -A m9999_g ) We have some instructions for setting your default allocation account in our Slurm Defaults Section
-q regular
debug
interactive
-A m9999_g
We have some instructions for setting your default allocation account in our Slurm Defaults Section
Please see our Running Jobs Section for examples and an explanation of new queue policies

## September 24, 2021 ¶

Upgraded internal management software
Upgraded system I/O forwarding software and moved it to a more performant network
Fixed csh environment
Performance profiling tool that request access to hardware counters (such as Nsight Compute) should work now

## September 16, 2021 ¶

Deployed numerous network upgrades and changes intended to increase responsiveness and performance
Increased robustness for login node load balancing

## September 10, 2021 ¶

Updated to CPE 21.09. A recompile is recommended but not required. Major changes of note include: Upgrade MPICH to 8.1.9 (from 8.1.8) Upgrade DSMML to 0.2.1 (from 0.2.0) Upgrade PALS to 1.0.17 (from 1.0.14) Upgrade OpenSHMEMX to 11.3.3 (from 11.3.2) Upgrade craype to 2.7.10 (from 2.7.9) Upgrade CCE to 12.0.3 (from 12.0.2) Upgrade HDF5 to 1.12.0.7 (from 1.12.0.6) GCC 11.2.0 added
Upgrade MPICH to 8.1.9 (from 8.1.8)
Upgrade DSMML to 0.2.1 (from 0.2.0)
Upgrade PALS to 1.0.17 (from 1.0.14)
Upgrade OpenSHMEMX to 11.3.3 (from 11.3.2)
Upgrade craype to 2.7.10 (from 2.7.9)
Upgrade CCE to 12.0.3 (from 12.0.2)
Upgrade HDF5 to 1.12.0.7 (from 1.12.0.6)
GCC 11.2.0 added
Added cuda module to the list of default modules loaded at startup
cuda
Set BASH_ENV to Lmod setup file
Deployed numerous network upgrades and changes intended to increase responsiveness and performance
Performed kernel upgrades to login nodes for better fail over support
Added latest CMake release as cmake/git-20210830 , and is set as the default cmake on the system
cmake/git-20210830
cmake

## September 2, 2021 ¶

Updated NVIDIA driver (to nvidia-gfxG04-kmp-default-450.142.00_k4.12.14_150.47-0.x86_64 ). This is not expected to have any user impact.
nvidia-gfxG04-kmp-default-450.142.00_k4.12.14_150.47-0.x86_64

## August 30, 2021 ¶


## Numerous changes to the NVIDIA programming environment ¶

Changed default NVIDIA compiler from 20.9 to 21.7
Installed needed CUDA compatibility libraries
Added support for multi-CUDA HPC SDK
Removed the cudatoolkit and craype-accel-nvidia80 modules from default
cudatoolkit
craype-accel-nvidia80
Tips for users:
Please use module load cuda and module av cuda to get the CUDA Toolkit, including the CUDA C compiler nvcc , and associated libraries and tools.
module load cuda
module av cuda
nvcc
CMake may have trouble picking up the correct mpich include files. If it does, you can use set ( CMAKE_CUDA_FLAGS "-I/opt/cray/pe/mpich/8.1.8/ofi/nvidia/20.7/include") to force it to pick up the correct one.
set ( CMAKE_CUDA_FLAGS "-I/opt/cray/pe/mpich/8.1.8/ofi/nvidia/20.7/include")

## June, 2021 ¶

Perlmutter achieved 64.6 Pflop/s (FP64 Tensor Core) using 1,424 compute nodes, putting it at No. 5 in the Top500 list .

## May 27, 2021 ¶

Perlmutter supercomputer dedication.

## November, 2020 - March, 2021 ¶

Perlmutter Phase 1 delivered.