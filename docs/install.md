Installation is as simple as:

```bash
pip install pydantic
```

*pydantic* has no required dependencies except Python 3.7, 3.8, 3.9, 3.10 or 3.11 and
[`typing-extensions`](https://pypi.org/project/typing-extensions/).
If you've got Python 3.7+ and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

## Optional dependencies

*pydantic* has the following optional dependencies:

* If you require email validation, you can add [email-validator](https://github.com/JoshData/python-email-validator).

To install optional dependencies along with *pydantic*:

```bash
pip install pydantic[email]
```

Of course, you can also install requirements manually with `pip install email-validator`.

## Install from repository

And if you prefer to install *pydantic* directly from the repository:

```bash
pip install git+git://github.com/pydantic/pydantic@main#egg=pydantic
# or with extras
pip install git+git://github.com/pydantic/pydantic@main#egg=pydantic[email]
```
