Installation is as simple as:

```bash
pip install pydantic
```

*pydantic* has no required dependencies except python 3.6, 3.7, 3.8, 3.9 or 3.10,
[`typing-extensions`](https://pypi.org/project/typing-extensions/), and the
[`dataclasses`](https://pypi.org/project/dataclasses/) backport package for python 3.6.
If you've got python 3.6+ and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

## Compiled with Cython

*pydantic* can optionally be compiled with [cython](https://cython.org/) which should give a 30-50% performance improvement. 

By default `pip install` provides optimized binaries via [PyPI](https://pypi.org/project/pydantic/#files) for Linux, MacOS and 64bit Windows.


If you're installing manually, install `cython` before installing *pydantic* and compilation should happen automatically.

To test if *pydantic* is compiled run:

```py
import pydantic
print('compiled:', pydantic.compiled)
```

### Performance vs package size trade-off

Compiled binaries can increase the size of your Python environment. If for some reason you want to reduce the size of your *pydantic* installation you can avoid installing any binaries using the [`pip --no-binary`](https://pip.pypa.io/en/stable/cli/pip_install/#install-no-binary) option. Make sure `Cython` is not in your environment, or that you have the `SKIP_CYTHON` environment variable set to avoid re-compiling *pydantic* libraries:

```bash
SKIP_CYTHON=1 pip install --no-binary pydantic pydantic
```
!!! note
    `pydantic` is repeated here intentionally, `--no-binary pydantic` tells `pip` you want no binaries for pydantic,
    the next `pydantic` tells `pip` which package to install.

Alternatively, you can re-compile *pydantic* with custom [build options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html), this would require having the [`Cython`](https://pypi.org/project/Cython/) package installed before re-compiling *pydantic* with:
```bash
CFLAGS="-Os -g0 -s" pip install \
  --no-binary pydantic \
  --global-option=build_ext \
  pydantic
```

## Optional dependencies

*pydantic* has two optional dependencies:

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


## Install from repository

And if you prefer to install *pydantic* directly from the repository:
```bash
pip install git+git://github.com/samuelcolvin/pydantic@master#egg=pydantic
# or with extras
pip install git+git://github.com/samuelcolvin/pydantic@master#egg=pydantic[email,dotenv]
```
