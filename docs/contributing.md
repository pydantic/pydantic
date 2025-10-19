We'd love you to contribute to Pydantic!

## Issues

Questions, feature requests and bug reports are all welcome as [discussions or issues](https://github.com/pydantic/pydantic/issues/new/choose).
**However, to report a security vulnerability, please see our [security policy](https://github.com/pydantic/pydantic/security/policy).**

To make it as simple as possible for us to help you, please include the output of the following call in your issue:

```bash
python -c "import pydantic.version; print(pydantic.version.version_info())"
```

If you're using Pydantic prior to **v2.0** please use:

```bash
python -c "import pydantic.utils; print(pydantic.utils.version_info())"
```

Please try to always include the above unless you're unable to install Pydantic or **know** it's not relevant
to your question or feature request.

## Pull Requests

It should be extremely simple to get started and create a Pull Request.
Pydantic is released regularly so you should see your improvements release in a matter of days or weeks 🚀.

Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
creating a pull request.

!!! note "Pydantic V1 is in maintenance mode"
    Pydantic v1 is in maintenance mode, meaning that only bug fixes and security fixes will be accepted.
    New features should be targeted at Pydantic v2.

    To submit a fix to Pydantic v1, use the `1.10.X-fixes` as a target branch.

If you're looking for something to get your teeth into, check out the
["help wanted"](https://github.com/pydantic/pydantic/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
label on github.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. Luckily,
Pydantic has few dependencies, doesn't require compiling and tests don't need access to databases, etc.
Because of this, setting up and running the tests should be very simple.

!!! tip
    **tl;dr**: use `make format` to fix formatting, `make` to run tests and linting and `make docs`
    to build the docs.

### Prerequisites

You'll need the following prerequisites:

* Any Python version between **Python 3.9 and 3.12**
* [**uv**](https://docs.astral.sh/uv/getting-started/installation/) or other virtual environment tool
* [**git**](https://git-scm.com/) - For version control
* [**make**](https://www.gnu.org/software/make/) - For running development commands (or use `nmake` on Windows)
* [**Rust**](https://rustup.rs/) - Rust stable (or nightly for coverage)

### Installation and setup

Fork the repository on GitHub and clone your fork locally.

```bash
# Clone your fork and cd into the repo directory
git clone git@github.com:<your username>/pydantic.git
cd pydantic

# Install UV and pre-commit
# We use pipx here, for other options see:
# https://docs.astral.sh/uv/getting-started/installation/
# https://pre-commit.com/#install
# To get pipx itself:
# https://pypa.github.io/pipx/
pipx install uv
pipx install pre-commit

# Install pydantic, dependencies, test dependencies and doc dependencies
make install
```

### Check out a new branch and make your changes

Create a new branch for your changes.

```bash
# Checkout a new branch and make your changes
git checkout -b my-new-feature-branch
# Make your changes...
```

### Run tests and linting

Run tests and linting locally to make sure everything is working as expected.

```bash
# Run automated code formatting and linting
make format
# Pydantic uses ruff, an awesome Python linter written in rust
# https://github.com/astral-sh/ruff

# Run tests and linting
make
# There are a few sub-commands in Makefile like `test`, `testcov` and `lint`
# which you might want to use, but generally just `make` should be all you need.
# You can run `make help` to see more options.
```

### Build documentation

If you've made any changes to the documentation (including changes to function signatures, class definitions, or docstrings that will appear in the API documentation), make sure it builds successfully.

We use `mkdocs-material[imaging]` to support social previews (see the [plugin documentation](https://squidfunk.github.io/mkdocs-material/plugins/requirements/image-processing/)).

```bash
# Build documentation
make docs
# If you have changed the documentation, make sure it builds successfully.
# You can also use `uv run mkdocs serve` to serve the documentation at localhost:8000
```

If this isn't working due to issues with the imaging plugin, try commenting out the `social` plugin line in `mkdocs.yml` and running `make docs` again.

#### Updating the documentation

We push a new version of the documentation with each minor release, and we push to a `dev` path with each commit to `main`.

If you're updating the documentation out of cycle with a minor release and want your changes to be reflected on `latest`,
do the following:

1. Open a PR against `main` with your docs changes
2. Once the PR is merged, checkout the `docs-update` branch. This branch should be up to date with the latest patch release.
For example, if the latest release is `v2.9.2`, you should make sure `docs-update` is up to date with the `v2.9.2` tag.
3. Checkout a new branch from `docs-update` and cherry-pick your changes onto this branch.
4. Push your changes and open a PR against `docs-update`.
5. Once the PR is merged, the new docs will be built and deployed.

!!! note
    Maintainer shortcut - as a maintainer, you can skip the second PR and just cherry pick directly onto the `docs-update` branch.

### Commit and push your changes

Commit your changes, push your branch to GitHub, and create a pull request.

Please follow the pull request template and fill in as much information as possible. Link to any relevant issues and include a description of your changes.

When your pull request is ready for review, add a comment with the message "please review" and we'll take a look as soon as we can.

## Documentation style

Documentation is written in Markdown and built using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). API documentation is build from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

### Code documentation

When contributing to Pydantic, please make sure that all code is well documented. The following should be documented using properly formatted docstrings:

* Modules
* Class definitions
* Function definitions
* Module-level variables

Pydantic uses [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) formatted according to [PEP 257](https://www.python.org/dev/peps/pep-0257/) guidelines. (See [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for further examples.)

[pydocstyle](https://www.pydocstyle.org/en/stable/index.html) is used for linting docstrings. You can run `make format` to check your docstrings.

Where this is a conflict between Google-style docstrings and pydocstyle linting, follow the pydocstyle linting hints.

Class attributes and function arguments should be documented in the format "name: description." When applicable, a return type should be documented with just a description. Types are inferred from the signature.

```python
class Foo:
    """A class docstring.

    Attributes:
        bar: A description of bar. Defaults to "bar".
    """

    bar: str = 'bar'
```

```python
def bar(self, baz: int) -> str:
    """A function docstring.

    Args:
        baz: A description of `baz`.

    Returns:
        A description of the return value.
    """

    return 'bar'
```

You may include example code in docstrings. This code should be complete, self-contained, and runnable. Docstring examples are tested, so make sure they are correct and complete. See [`BeforeValidator`][pydantic.functional_validators.AfterValidator] for an example.

!!! note "Class and instance attributes"
    Class attributes should be documented in the class docstring.

    Instance attributes should be documented as "Args" in the `__init__` docstring.

### Documentation Style

In general, documentation should be written in a friendly, approachable style. It should be easy to read and understand, and should be as concise as possible while still being complete.

Code examples are encouraged, but should be kept short and simple. However, every code example should be complete, self-contained, and runnable. (If you're not sure how to do this, ask for help!) We prefer print output to naked asserts, but if you're testing something that doesn't have a useful print output, asserts are fine.

Pydantic's unit test will test all code examples in the documentation, so it's important that they are correct and complete. When adding a new code example, use the following to test examples and update their formatting and output:

```bash
# Run tests and update code examples
pytest tests/test_docs.py --update-examples
```

## Debugging Python and Rust

If you're working with `pydantic` and `pydantic-core`, you might find it helpful to debug Python and Rust code together.
Here's a quick guide on how to do that. This tutorial is done in VSCode, but you can use similar steps in other IDEs.

<div style="position: relative; padding-bottom: 56.4035546262415%; height: 0;">
    <iframe src="https://www.loom.com/embed/71019f8b92b04839ae233eb70c23c5b5?sid=1ea39ca9-d0cc-494b-8214-159f7cc26190" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
</div>

## Badges

[![Pydantic v1](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json)](https://pydantic.dev)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)

Pydantic has a badge that you can use to show that your project uses Pydantic. You can use this badge in your `README.md`:

### With Markdown

```md
[![Pydantic v1](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json)](https://pydantic.dev)

[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
```

### With reStructuredText

```rst
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json
    :target: https://pydantic.dev
    :alt: Pydantic

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json
    :target: https://pydantic.dev
    :alt: Pydantic
```

### With HTML

```html
<a href="https://pydantic.dev"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json" alt="Pydantic Version 1" style="max-width:100%;"></a>

<a href="https://pydantic.dev"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json" alt="Pydantic Version 2" style="max-width:100%;"></a>
```

## Adding your library as part of Pydantic's third party test suite

To be able to identify regressions early during development, Pydantic runs tests on various third-party projects
using Pydantic. We consider adding support for testing new open source projects (that rely heavily on Pydantic) if your said project matches some of the following criteria:

* The project is actively maintained.
* The project makes use of Pydantic internals (e.g. relying on the [`BaseModel`][pydantic.BaseModel] metaclass, typing utilities).
* The project is popular enough (although small projects can still be included depending on how Pydantic is being used).
* The project CI is simple enough to be ported into Pydantic's testing workflow.

If your project meets some of these criteria, you can [open feature request][open feature request]
to discuss the inclusion of your project.

[open feature request]: https://github.com/pydantic/pydantic/issues/new?assignees=&labels=feature+request&projects=&template=feature_request.yml
