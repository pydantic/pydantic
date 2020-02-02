Installation is as simple as:

```py
pip install pydantic
```

*pydantic* has no required dependencies except python 3.6, 3.7, or 3.8 (and the dataclasses package in python 3.6).
If you've got python 3.6+ and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

*pydantic* can optionally be compiled with [cython](https://cython.org/) which should give a 30-50% performance
improvement. `manylinux` binaries exist for python 3.6, 3.7, and 3.8, so if you're installing from PyPI on linux, you
should get a compiled version of *pydantic* with no extra work. If you're installing manually, install `cython`
before installing *pydantic* and compilation should happen automatically. Compilation with cython
[is not tested](https://github.com/samuelcolvin/pydantic/issues/555) on windows or mac.

To test if *pydantic* is compiled run:

```py
import pydantic
print('compiled:', pydantic.compiled)
```

*pydantic* has three optional dependencies:

* If you require email validation you can add [email-validator](https://github.com/JoshData/python-email-validator)
* use of `Literal` prior to python 3.8 relies on [typing-extensions](https://pypi.org/project/typing-extensions/)
* [dotenv file support](usage/settings.md#dotenv-env-support) with `Settings` requires
  [python-dotenv](https://pypi.org/project/python-dotenv)

To install these along with *pydantic*:
```bash
pip install pydantic[email]
# or
pip install pydantic[typing_extensions]
# or
pip install pydantic[dotenv]
# or just
pip install pydantic[email,typing_extensions,dotenv]
```

Of course, you can also install these requirements manually with `pip install email-validator` and/or `pip install typing_extensions`.

And if you prefer to install *pydantic* directly from the repository:
```bash
pip install git+git://github.com/samuelcolvin/pydantic@master#egg=pydantic
# or with extras
pip install git+git://github.com/samuelcolvin/pydantic@master#egg=pydantic[email,typing_extensions]
```
