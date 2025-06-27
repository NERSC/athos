This is a very simple issue where a user's job settings are not supported.
In particular, the job is requesting the 'debug' qos but asking for an 8 hour
time limit. This page shows that debug jobs have a max wall time of 30min:
https://docs.nersc.gov/jobs/policy/#perlmutter-gpu
