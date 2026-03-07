# Source: https://docs.nersc.gov/development/containers/

## Containers ¶

Containers provide a stable fixed environment for your software that greatly reduces the dependency on any details of NERSC's software stack while retaining and, in some cases, improving performance.
If your application depends on MPI, then NERSC recommends installing MPICH inside the container from source (i.e. not from apt-get ) with shared libraries. This allows your software to use the ABI-compatible Cray MPICH which has been optimized for the Perlmutter network.
apt-get
Users are welcome and encouraged to use containers to run their software on NERSC systems. To facilitate this, NERSC provides various container technologies.
We provide a page of Tips and Tricks for transitioning between podman-hpc and Shifter should the need arise.

## podman-hpc ¶

podman-hpc
podman-hpc , an adaptation of Podman for HPC use-cases, is available on Perlmutter and offers several advantages over the Shifter tool, including the ability to create containers on Perlmutter. This capability is available because Podman utilizes usernamespaces which have, unfortunately, been less reliable and performant at scale than desired.
podman-hpc

## Shifter ¶

Shifter is a NERSC-developed tool which allows users to run images on NERSC systems such as Perlmutter.
Shifter

## Building Custom Images ¶

The page, Building Custom Images provides details of the base image that can be used as a starting point to develop your own container image. It also provides various building blocks that can be used as a template to develop your own.

## registry.nersc.gov ¶

registry.nersc.gov
NERSC offers a private image registry where users can store images. We offer information about and best practices for using the registry .