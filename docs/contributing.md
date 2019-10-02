We'd love you to contribute to *pydantic*, it should be extremely simple to get started and create a Pull Request.
*pydantic* is released regularly so you should see your improvements release in a matter of days or weeks.

Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
creating a pull request.

If you're looking for something to get your teeth into, check out the
["help wanted"](https://github.com/samuelcolvin/pydantic/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
label on github.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. Luckily since
*pydantic* has few dependencies, doesn't require compiling and tests don't need access to databases etc., setting
up and running tests should be very simple.

You'll need to have **python 3.6** or **3.7**, **virtualenv**, **git**, and **make** installed.

```bash
{!./examples/contributing.sh!}
```

**tl;dr**: use `make format` to fix formatting, `make` to run tests and linting & `make docs`
to build docs.
