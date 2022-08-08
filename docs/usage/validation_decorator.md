The `validate_arguments` decorator allows the arguments passed to a function to be parsed and validated using
the function's annotations before the function is called. While under the hood this uses the same approach of model
creation and initialisation; it provides an extremely easy way to apply validation to your code with minimal
boilerplate.

!!! info "In Beta"
    The `validate_arguments` decorator is in **beta**, it has been added to *pydantic* in **v1.5** on a
    **provisional basis**. It may change significantly in future releases and its interface will not be concrete
    until **v2**. Feedback from the community while it's still provisional would be extremely useful; either comment
    on [#1205](https://github.com/pydantic/pydantic/issues/1205) or create a new issue.

Example of usage:

```py
{!.tmp_examples/validation_decorator_main.py!}
```
_(This script is complete, it should run "as is")_

## Argument Types

Argument types are inferred from type annotations on the function, arguments without a type decorator are considered
as `Any`. Since `validate_arguments` internally uses a standard `BaseModel`, all types listed in
[types](types.md) can be validated, including *pydantic* models and [custom types](types.md#custom-data-types).
As with the rest of *pydantic*, types can be coerced by the decorator before they're passed to the actual function:

```py
{!.tmp_examples/validation_decorator_types.py!}
```
_(This script is complete, it should run "as is")_

A few notes:

- though they're passed as strings, `path` and `regex` are converted to a `Path` object and regex respectively
by the decorator
- `max` has no type annotation, so will be considered as `Any` by the decorator

Type coercion like this can be extremely helpful but also confusing or not desired,
see [below](#coercion-and-strictness) for a discussion of `validate_arguments`'s limitations in this regard.

## Function Signatures

The decorator is designed to work with functions using all possible parameter configurations and all possible
combinations of these:

* positional or keyword arguments with or without defaults
* variable positional arguments defined via `*` (often `*args`)
* variable keyword arguments defined via `**` (often `**kwargs`)
* keyword only arguments - arguments after `*,`
* positional only arguments - arguments before `, /` (new in Python 3.8)

To demonstrate all the above parameter types:

```py
{!.tmp_examples/validation_decorator_parameter_types.py!}
```
_(This script is complete, it should run "as is")_

## Using Field to describe function arguments

[Field](schema.md#field-customisation) can also be used with `validate_arguments` to provide extra information about
the field and validations. In general it should be used in a type hint with
[Annotated](schema.md#typingannotated-fields), unless `default_factory` is specified, in which case it should be used
as the default value of the field:

```py
{!.tmp_examples/validation_decorator_field.py!}
```
_(This script is complete, it should run "as is")_

The [alias](model_config#alias-precedence) can be used with the decorator as normal.

```py
{!.tmp_examples/validation_decorator_field_alias.py!}
```
_(This script is complete, it should run "as is")_

## Usage with mypy

The `validate_arguments` decorator should work "out of the box" with [mypy](http://mypy-lang.org/) since it's
defined to return a function with the same signature as the function it decorates. The only limitation is that
since we trick mypy into thinking the function returned by the decorator is the same as the function being
decorated; access to the [raw function](#raw-function) or other attributes will require `type: ignore`.

## Validate without calling the function

By default, arguments validation is done by directly calling the decorated function with parameters.
But what if you wanted to validate them without *actually* calling the function?
To do that you can call the `validate` method bound to the decorated function.

```py
{!.tmp_examples/validation_decorator_validate.py!}
```
_(This script is complete, it should run "as is")_

## Raw function

The raw function which was decorated is accessible, this is useful if in some scenarios you trust your input
arguments and want to call the function in the most performant way (see [notes on performance](#performance) below):

```py
{!.tmp_examples/validation_decorator_raw_function.py!}
```
_(This script is complete, it should run "as is")_

## Async Functions

`validate_arguments` can also be used on async functions:

```py
{!.tmp_examples/validation_decorator_async.py!}
```

## Custom Config

The model behind `validate_arguments` can be customised using a config setting which is equivalent to
setting the `Config` sub-class in normal models.

!!! warning
    The `fields` and `alias_generator` properties of `Config` which allow aliases to be configured are not supported
    yet with `@validate_arguments`, using them will raise an error.

Configuration is set using the `config` keyword argument to the decorator, it may be either a config class
or a dict of properties which are converted to a class later.

```py
{!.tmp_examples/validation_decorator_config.py!}
```
_(This script is complete, it should run "as is")_

## Limitations

`validate_arguments` has been released on a provisional basis without all the bells and whistles, which may
be added later, see [#1205](https://github.com/pydantic/pydantic/issues/1205) for some more discussion of this.

In particular:

### Validation Exception

Currently upon validation failure, a standard *pydantic* `ValidationError` is raised,
see [model error handling](models.md#error-handling).

This is helpful since it's `str()` method provides useful details of the error which occurred and methods like
`.errors()` and `.json()` can be useful when exposing the errors to end users, however `ValidationError` inherits
from `ValueError` **not** `TypeError` which may be unexpected since Python would raise a `TypeError` upon invalid
or missing arguments. This may be addressed in future by either allow a custom error or raising a different
exception by default, or both.

### Coercion and Strictness

*pydantic* currently leans on the side of trying to coerce types rather than raise an error if a type is wrong,
see [model data conversion](models.md#data-conversion) and `validate_arguments` is no different.

See [#1098](https://github.com/pydantic/pydantic/issues/1098) and other issues with the "strictness" label
for a discussion of this. If *pydantic* gets a "strict" mode in future, `validate_arguments` will have an option
to use this, it may even become the default for the decorator.

### Performance

We've made a big effort to make *pydantic* as performant as possible
and argument inspect and model creation is only performed once when the function is defined, however
there will still be a performance impact to using the `validate_arguments` decorator compared to
calling the raw function.

In many situations this will have little or no noticeable effect, however be aware that
`validate_arguments` is not an equivalent or alternative to function definitions in strongly typed languages;
it never will be.

### Return Value

The return value of the function is not validated against its return type annotation, this may be added as an option
in future.

### Config and Validators

`fields` and `alias_generator` on custom [`Config`](model_config.md) are not supported, see [above](#custom-config).

Neither are [validators](validators.md).

### Model fields and reserved arguments

The following names may not be used by arguments since they can be used internally to store information about
the function's signature:

* `v__args`
* `v__kwargs`
* `v__positional_only`

These names (together with `"args"` and `"kwargs"`) may or may not (depending on the function's signature) appear as
fields on the internal *pydantic* model accessible via `.model` thus this model isn't especially useful
(e.g. for generating a schema) at the moment.

This should be fixable in future as the way error are raised is changed.
