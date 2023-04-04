# requirements

This folder contains requirements files (`*.in` files) that get compiled into lockfiles (`*.txt` files) by [pip-tools].

All of the `*.in` files get collected into `all.in`, which then crates `all.txt`. This `all.txt` functions both as the pip-installable requirements file with all of the requirements and as a [pip constraints file](https://pip.pypa.io/en/stable/user_guide/#constraints-files) for the rest of the lockfiles. This ensures that all of the lockfiles lock to the same version of dependencies and are compatible (that is, you can always install any combination of lockfiles without dependency version conflicts).
The individual lockfiles, for example `docs.txt`, get produced by combining `docs.in` with `all.txt` via `docs-constrained.in`. This is necessary because pip-tools can only accept lockfiles if they are specified in a requirements file, but we cannot but the reference to `all.txt` in `docs.in` because `docs.in` is used to build `all.txt`.

There are two scripts included: `rebuild.sh` which deletes the lockfiles and rebuilds them from scratch (thus updating all dependencies) and `refresh.sh` which updates the lockfiles to reflect any changes in the `.in` files while minimizing the changes to the lockfiles (i.e. it only updates/changes dependencies that need updating/changing).

[pip-tools]: https://github.com/jazzband/pip-tools
