This failure occurs because the user is not authorized for the `desi` allocation account. Slurm checks your allocation membership whenever you pass `-A desi`. If you are not in that account, the request is rejected with a policy error.

Run the `iris` command to list the allocation accounts you belong to and confirm whether `desi` appears. If it does not, ask the account PI or an authorized proxy to add you. After they add you, the corresponding Unix group membership and Slurm authorization can take up to 30 minutes to propagate before `salloc` succeeds.

You can also run `groups` to see which allocation groups have already propagated to your session.
