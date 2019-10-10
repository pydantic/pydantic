Installation is as simple as:

```py
pip install pydantic
```

*pydantic* has no required dependencies except python 3.6 or 3.7 (and the dataclasses package in python 3.6).
If you've got python 3.6 and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

*pydantic* can optionally be compiled with [cython](https://cython.org/) which should give a 30-50% performance
improvement. `manylinux` binaries exist for python 3.6 and 3.7, so if you're installing from PyPI on linux, you
should get a compiled version of *pydantic* with no extra work. If you're installing manually, install `cython`
before installing *pydantic* and compilation should happen automatically. Compilation with cython
[is not tested](https://github.com/samuelcolvin/pydantic/issues/555) on windows or mac.

To test if *pydantic* is compiled run:

```py
import pydantic
print('compiled:', pydantic.compiled)
```

If you require email validation you can add [email-validator](https://github.com/JoshData/python-email-validator)
as an optional dependency. Similarly, use of `Literal` relies on
[typing-extensions](https://pypi.org/project/typing-extensions/):

```bash
pip install pydantic[email]
# or
pip install pydantic[typing_extensions]
# or just
pip install pydantic[email,typing_extensions]
```

Of course, you can also install these requirements manually with `pip install ...`.
