Installation is as simple as:

```bash
pip install pydantic
```

*pydantic* has no required dependencies except python 3.6, 3.7, 3.8, or 3.9,
[`typing-extensions`](https://pypi.org/project/typing-extensions/), and the
[`dataclasses`](https://pypi.org/project/dataclasses/) backport package for python 3.6.
If you've got python 3.6+ and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

*pydantic* can optionally be compiled with [cython](https://cython.org/) which should give a 30-50% performance
improvement. 

Binaries are available from [PyPI](https://pypi.org/project/pydantic/#files) for Linux, MacOS and 64bit Windows.
If you're installing manually, install `cython` before installing *pydantic* and compilation should happen automatically.

To test if *pydantic* is compiled run:

```py
import pydantic
print('compiled:', pydantic.compiled)
```

*pydantic* has three optional dependencies:

* If you require email validation you can add [email-validator](https://github.com/JoshData/python-email-validator)
* [dotenv file support](usage/settings.md#dotenv-env-support) with `Settings` requires
  [python-dotenv](https://pypi.org/project/python-dotenv)

To install these along with *pydantic*:
```bash
pip install pydantic[email]
# or
pip install pydantic[dotenv]
# or just
pip install pydantic[email,dotenv]
```

Of course, you can also install these requirements manually with `pip install email-validator` and/or `pip install`.

And if you prefer to install *pydantic* directly from the repository:
```bash
pip install git+git://github.com/samuelcolvin/pydantic@master#egg=pydantic
# or with extras
pip install git+git://github.com/samuelcolvin/pydantic@master#egg=pydantic[email,dotenv]
```
