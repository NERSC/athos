In this issue, the user is using the default huggingface cache path,
which is in the home directory and will cause a known issue on the compute nodes.
We use DVS to mount this filesystem, which doesn't support file locking,
which causes a hang when huggingface tries to download things there.

The fix is to move the cache directory to scratch, by doing something like

```
export HF_HOME=$SCRATCH/cache/huggingface
```
