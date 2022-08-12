We'd love you to contribute to *pydantic*!

## Issues

Questions, feature requests and bug reports are all welcome as [discussions or issues](https://github.com/pydantic/pydantic/issues/new/choose). **However, to report a security
vulnerability, please see our [security policy](https://github.com/pydantic/pydantic/security/policy).**

To make it as simple as possible for us to help you, please include the output of the following call in your issue:

```bash
python -c "import pydantic.utils; print(pydantic.utils.version_info())"
```
If you're using *pydantic* prior to **v1.3** (when `version_info()` was added), please manually include OS, Python
version and pydantic version.

Please try to always include the above unless you're unable to install *pydantic* or **know** it's not relevant
to your question or feature request.

## Pull Requests

It should be extremely simple to get started and create a Pull Request.
*pydantic* is released regularly so you should see your improvements release in a matter of days or weeks.

!!! note
    Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
    creating a pull request.

If you're looking for something to get your teeth into, check out the
["help wanted"](https://github.com/pydantic/pydantic/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
label on github.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. Luckily,
*pydantic* has few dependencies, doesn't require compiling and tests don't need access to databases, etc.
Because of this, setting up and running the tests should be very simple.

You'll need to have a version between **Python 3.7 and 3.10**, **virtualenv**, **git**, and **make** installed.

```bash
# 1. clone your fork and cd into the repo directory
git clone git@github.com:<your username>/pydantic.git
cd pydantic

# 2. Set up a virtualenv for running tests
virtualenv -p `which python3.8` env
source env/bin/activate
# Building docs requires 3.8. If you don't need to build docs you can use
# whichever version; 3.7 will work too.

# 3. Install pydantic, dependencies, test dependencies and doc dependencies
make install

# 4. Checkout a new branch and make your changes
git checkout -b my-new-feature-branch
# make your changes...

# 5. Fix formatting and imports
make format
# Pydantic uses black to enforce formatting and isort to fix imports
# (https://github.com/ambv/black, https://github.com/timothycrosley/isort)

# 6. Run tests and linting
make
# there are a few sub-commands in Makefile like `test`, `testcov` and `lint`
# which you might want to use, but generally just `make` should be all you need

# 7. Build documentation
make docs
# if you have changed the documentation make sure it builds successfully
# you can also use `make docs-serve` to serve the documentation at localhost:8000

# ... commit, push, and create your pull request
```

**tl;dr**: use `make format` to fix formatting, `make` to run tests and linting & `make docs`
to build the docs.
