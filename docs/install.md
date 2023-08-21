Installation is as simple as:

```bash
pip install pydantic
```

Pydantic has a few dependencies:

* [`pydantic-core`](https://pypi.org/project/pydantic-core/): Core validation logic for _pydantic_ written in rust.
* [`typing-extensions`](https://pypi.org/project/typing-extensions/): Backport of the standard library `typing` module.
* [`annotated-types`](https://pypi.org/project/annotated-types/): Reusable constraint types to use with `typing.Annotated`.

If you've got Python 3.8+ and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

## Optional dependencies

Pydantic has the following optional dependencies:

* If you require email validation, you can add [email-validator](https://github.com/JoshData/python-email-validator).

To install optional dependencies along with Pydantic:

```bash
pip install pydantic[email]
```

Of course, you can also install requirements manually with `pip install email-validator`.

## Install from repository

And if you prefer to install Pydantic directly from the repository:

```bash
pip install git+https://github.com/pydantic/pydantic@main#egg=pydantic
# or with extras
pip install git+https://github.com/pydantic/pydantic@main#egg=pydantic[email]
```
