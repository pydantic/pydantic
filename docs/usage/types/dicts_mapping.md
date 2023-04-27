# Dicts and Mapping Types

`dict`
: `dict(v)` is used to attempt to convert a dictionary;
  see `typing.Dict` below for sub-type constraints

`typing.Dict`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`subclass of typing.TypedDict`
: Same as `dict` but _pydantic_ will validate the dictionary since keys are annotated.
  See [Annotated Types](#annotated-types) below for more detail on parsing and validation

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.
    But required and optional fields are properly differentiated only since Python 3.9.
    We therefore recommend using [typing-extensions](https://pypi.org/project/typing-extensions/) with Python 3.8 as well.
