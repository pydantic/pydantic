The `validate_assignment` decorator allows the arguments passed to a function to be parsed and validated using
the function's annotations before the function is called. While under the hood this uses the same approach of model
creation and initialisation; it provides an extremely easy way to apply validation to your code with minimal
boilerplate.

!!! warning
    The `validate_assignment` decorator is in **beta**, it has been added to *pydantic* in **v1.5** on a
    **provisional basis**. It may change significantly in future releases and its interface will not be concrete
    until **v2**. Feedback from the community while it's still provisional would be extremely useful; either comment
    on [#1205](https://github.com/samuelcolvin/pydantic/issues/1205) or create a new issue.

Example of usage:

```py
{!.tmp_examples/validation_decorator_main.py!}
```
_(This script is complete, it should run "as is")_

## Argument Configuration

The decorator is designed to work with functions using all possible parameter configurations:

* positional or keyword arguments with or without defaults (e.g. `s` or `count` in the above example)
* variable positional arguments defined via `*` (often `*args`)
* variable key word arguments defined via `**` (often `**kwargs`)
* keyword only arguments - arguments after `*,`
* positional only arguments - arguments before `/,` (new in python 3.8)

To demonstrate all the above parameter types:

```py
{!.tmp_examples/validation_decorator_parameter_types.py!}
```
_(This script is complete, it should run "as is")_

## Argument Types

all should work, see [types](types.md), custom types should work

Include example or path and PositiveInt

## Limitations

Will be extended in future, please comment or consider implementing one of these features

* raises `ValidationError`
* coercion
* performance
* return type is not validated

## Usage with mypy

effort has been made, should work

## Advanced Usage

accessing the underlying model.
