# D3M datasets

Please report issues on [MIT-LL's repository](https://gitlab.datadrivendiscovery.org/MIT-LL/d3m_data_supply/issues).

## Downloading

Download datasets using [git LFS](https://git-lfs.github.com/):

```
$ git lfs clone git@gitlab.datadrivendiscovery.org:d3m/datasets.git
```

Note, use `git lfs clone` instead of `git clone` because it
is faster.

This will take time but especially disk space. Currently all
datasets are around 54 GB, but the whole directory with cloned
repository and git metadata is around 84 GB. Running
`git lfs prune` might help by removing old and unreferenced files.

Repository is organized so that all files larger than 100 KB are
stored in git LFS, while smaller files are managed through git
directly. This makes cloning faster because there is no need
to make many HTTP requests for small git LFS files which is slow.

## Partial downloading

It is possible to download only part of the repository. First clone
without downloading files managed by git LFS:

```
$ git lfs clone git@gitlab.datadrivendiscovery.org:d3m/datasets.git -X "*"
```

This will download and checkout all files smaller than 100 KB.

Now to download all files of one dataset, run inside cloned repository:

```
$ git lfs pull -I seed_datasets_current/185_baseball_MIN_METADATA/
```
