We'd love you to contribute to Pydantic!

## Issues

Questions, feature requests and bug reports are all welcome as [discussions or issues](https://github.com/pydantic/pydantic/issues/new/choose). **However, to report a security
vulnerability, please see our [security policy](https://github.com/pydantic/pydantic/security/policy).**

To make it as simple as possible for us to help you, please include the output of the following call in your issue:

```bash
python -c "import pydantic.utils; print(pydantic.utils.version_info())"
```
If you're using Pydantic prior to **v1.3** (when `version_info()` was added), please manually include OS, Python
version and pydantic version.

Please try to always include the above unless you're unable to install Pydantic or **know** it's not relevant
to your question or feature request.

## Pull Requests

It should be extremely simple to get started and create a Pull Request.
Pydantic is released regularly so you should see your improvements release in a matter of days or weeks.

Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
creating a pull request.

!!! note "Pydantic V1 is in maintenance mode"
    Pydantic v1 is in maintenance mode, meaning that only bug fixes and security fixes will be accepted.
    New features should be targeted at Pydantic v2.

    To submit a fix to Pydantic v1, use the `1.10.X-fixes` branch.

If you're looking for something to get your teeth into, check out the
["help wanted"](https://github.com/pydantic/pydantic/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
label on github.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. Luckily,
Pydantic has few dependencies, doesn't require compiling and tests don't need access to databases, etc.
Because of this, setting up and running the tests should be very simple.

!!! tip
    **tl;dr**: use `make format` to fix formatting, `make` to run tests and linting & `make docs`
    to build the docs.

### Prerequisites

You'll need the following prerequisites:

- Any Python version between **Python 3.7 and 3.11**
- **virtualenv** or other virtual environment tool
- **git**
- **make**
- [**PDM**](https://pdm.fming.dev/latest/#installation)

### Installation and setup

Fork the repository on GitHub and clone your fork locally.

```bash
# Clone your fork and cd into the repo directory
git clone git@github.com:<your username>/pydantic.git
cd pydantic

# Install PDM and pre-commit
# We use pipx here, for other options see:
# https://pdm.fming.dev/latest/#installation
# https://pre-commit.com/#install
# To get pipx itself:
# https://pypa.github.io/pipx/
pipx install pdm pre-commit

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
# Pydantic uses black and ruff
# (https://github.com/ambv/black, https://github.com/charliermarsh/ruff)

# Run tests and linting
make
# There are a few sub-commands in Makefile like `test`, `testcov` and `lint`
# which you might want to use, but generally just `make` should be all you need.
# You can run `make help` to see more options.
```

### Build documentation

If you've made any changes to the documentation (including changes to function signatures, class definitions, or docstrings that will appear in the API documentation), make sure it builds successfully.

```bash
# Build documentation
make docs
# If you have changed the documentation, make sure it builds successfully.
# You can also use `make docs-serve` to serve the documentation at localhost:8000
```

### Commit and push your changes

Commit your changes, push your branch to GitHub, and create a pull request.

Please follow the pull request template and fill in as much information as possible. Link to any relevant issues and include a description of your changes.

When your pull request is ready for review, add a comment with the message "please review" and we'll take a look as soon as we can.

## Code style and requirements

TODO

## Documentation style

Documentation is written in Markdown and built using Material for MkDocs.

In general, documentation should be written in a friendly, approachable style. It should be easy to read and understand, and should be as concise as possible while still being complete.

Code examples are encouraged, but should be kept short and simple. However, every code example should be complete, self-contained, and runnable. (If you're not sure how to do this, ask for help!) We prefer print output to naked asserts, but if you're testing something that doesn't have a useful print output, asserts are fine.

Pydantic's test coverage will test all code examples in the documentation, so it's important that they are correct and complete. When adding a new code example, use `pytest --update-examples` to update the output and create Python version-specific examples when appropriate.

```bash
# Run tests and update code examples
pytest --update-examples
```

### Code documentation

Modules, classes, functions, and module-level variables should be documented using docstrings formatted according to [PEP 257](https://www.python.org/dev/peps/pep-0257/). Type annotations should be used wherever possible.

Pydantic uses [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for all docstrings. (See [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for further examples.)
