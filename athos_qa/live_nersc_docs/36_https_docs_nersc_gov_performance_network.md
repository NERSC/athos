# Source: https://docs.nersc.gov/performance/network/

## Network ¶


## Perlmutter Slingshot Interconnect ¶

Perlmutter uses Slingshot, a high-performance networking interconnect technology developed by Hewlett Packard Enterprise (HPE). The hardware component of Perlmutter's Slingshot interconnect is described in more detail on the Perlmutter Architechture page . We will track some user-tunable features of the Slingshot host software (SHS) here. In general more details can be found in the intro_mpi man page ( man intro_mpi ).
intro_mpi
man intro_mpi

## Adjusting message matching mode ¶

Hardware message matching is a powerful tool for improving the performance, efficiency, and reliability of HPC network communication. It typically involves the use of specialized hardware components that are optimized for high-speed data processing. These components can perform message matching operations in real-time, enabling high-speed data transfer and processing in complex systems.
By default, SHS is set to use hardware message matching and only switch over to (slower) software message matching when the hardware counters are full. This is controlled by setting the environment variable FI_CXI_RX_MATCH_MODE to hybrid . This ensures that codes that generate many MPI messages will continue to function once they've filled up the hardware queues on the Network Interface Cards (albeit at a slower rate). This comes at the cost of a slight overhead in memory usage. The exact value depends on the number of ranks and the size of each request buffer, but will generally be less than 2% of the existing memory on the node. If users wish to default to only using hardware message matching, they can set FI_CXI_RX_MATCH_MODE=hardware .
FI_CXI_RX_MATCH_MODE
hybrid
FI_CXI_RX_MATCH_MODE=hardware
Defaulting to pure hardware mode can cause jobs to fail Setting FI_CXI_RX_MATCH_MODE=hardware can cause jobs to fail when they exhaust the hardware message queue (usually by sending too many MPI messages). If this happens, the job will fail with a message like LE resources not recovered during flow control. FI_CXI_RX_MATCH_MODE=[hybrid|software] is required .
Setting FI_CXI_RX_MATCH_MODE=hardware can cause jobs to fail when they exhaust the hardware message queue (usually by sending too many MPI messages). If this happens, the job will fail with a message like LE resources not recovered during flow control. FI_CXI_RX_MATCH_MODE=[hybrid|software] is required .
FI_CXI_RX_MATCH_MODE=hardware
LE resources not recovered during flow control. FI_CXI_RX_MATCH_MODE=[hybrid|software] is required

## Network Performance Report ¶

If desired, SHS can collect network data such as the number of network timeouts and counter data for Network Interface Cards during an MPI job. Often times it's difficult to put these reports in context for a single job, but if you wish to enable this report, it can be done by setting the environment variable MPICH_OFI_CXI_COUNTER_REPORT to a value between 1 and 5. See man intro_mpi for a list of the different reporting levels available. Please note if there are no network timeouts, no extra information will be printed.
MPICH_OFI_CXI_COUNTER_REPORT
man intro_mpi