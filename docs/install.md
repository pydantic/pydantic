Installation is as simple as:

=== "pip"

    ```bash
    pip install pydantic
    ```

=== "uv"

    ```bash
    uv add pydantic
    ```

Pydantic has a few dependencies:

* [`pydantic-core`](https://pypi.org/project/pydantic-core/): Core validation logic for Pydantic written in Rust.
* [`typing-extensions`](https://pypi.org/project/typing-extensions/): Backport of the standard library [typing][] module.
* [`annotated-types`](https://pypi.org/project/annotated-types/): Reusable constraint types to use with [`typing.Annotated`][].

If you've got Python 3.8+ and `pip` installed, you're good to go.

Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org)
channel:

```bash
conda install pydantic -c conda-forge
```

## Optional dependencies

Pydantic has the following optional dependencies:

* `email`: Email validation provided by the [email-validator](https://pypi.org/project/email-validator/) package.
* `timezone`: Fallback IANA time zone database provided by the [tzdata](https://pypi.org/project/tzdata/) package.

To install optional dependencies along with Pydantic:


=== "pip"

    ```bash
    # with the `email` extra:
    pip install 'pydantic[email]'
    # or with `email` and `timezone` extras:
    pip install 'pydantic[email,timezone]'
    ```

=== "uv"

    ```bash
    # with the `email` extra:
    uv add 'pydantic[email]'
    # or with `email` and `timezone` extras:
    uv add 'pydantic[email,timezone]'
    ```

Of course, you can also install requirements manually with `pip install email-validator tzdata`.

## Install from repository

And if you prefer to install Pydantic directly from the repository:


=== "pip"

    ```bash
    pip install 'git+https://github.com/pydantic/pydantic@main'
    # or with `email` and `timezone` extras:
    pip install 'git+https://github.com/pydantic/pydantic@main#egg=pydantic[email,timezone]'
    ```

=== "uv"

    ```bash
    uv add 'git+https://github.com/pydantic/pydantic@main'
    # or with `email` and `timezone` extras:
    uv add 'git+https://github.com/pydantic/pydantic@main#egg=pydantic[email,timezone]'
    ```
