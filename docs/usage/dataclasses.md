If you don't want to use _pydantic_'s `BaseModel` you can instead get the same data validation on standard
[dataclasses](https://docs.python.org/3/library/dataclasses.html) (introduced in Python 3.7).

```py
{!.tmp_examples/dataclasses_main.py!}
```
_(This script is complete, it should run "as is")_

!!! note
    Keep in mind that `pydantic.dataclasses.dataclass` is a drop-in replacement for `dataclasses.dataclass`
    with validation, **not** a replacement for `pydantic.BaseModel` (with a small difference in how [initialization hooks](#initialize-hooks) work). There are cases where subclassing
    `pydantic.BaseModel` is the better choice.

    For more information and discussion see
    [samuelcolvin/pydantic#710](https://github.com/pydantic/pydantic/issues/710).

You can use all the standard _pydantic_ field types, and the resulting dataclass will be identical to the one
created by the standard library `dataclass` decorator.

The underlying model and its schema can be accessed through `__pydantic_model__`.
Also, fields that require a `default_factory` can be specified by either a `pydantic.Field` or a `dataclasses.field`.

```py
{!.tmp_examples/dataclasses_default_schema.py!}
```
_(This script is complete, it should run "as is")_

`pydantic.dataclasses.dataclass`'s arguments are the same as the standard decorator, except one extra
keyword argument `config` which has the same meaning as [Config](model_config.md).

!!! warning
    After v1.2, [The Mypy plugin](../mypy_plugin.md) must be installed to type check _pydantic_ dataclasses.

For more information about combining validators with dataclasses, see
[dataclass validators](validators.md#dataclass-validators).

## Dataclass Config

If you want to modify the `Config` like you would with a `BaseModel`, you have three options:

```py
{!.tmp_examples/dataclasses_config.py!}
```

!!! warning
    After v1.10, _pydantic_ dataclasses support `Config.extra` but some default behaviour of stdlib dataclasses
    may prevail. For example, when `print`ing a _pydantic_ dataclass with allowed extra fields, it will still
    use the `__str__` method of stdlib dataclass and show only the required fields.
    This may be improved further in the future.

## Nested dataclasses

Nested dataclasses are supported both in dataclasses and normal models.

```py
{!.tmp_examples/dataclasses_nested.py!}
```
_(This script is complete, it should run "as is")_

Dataclasses attributes can be populated by tuples, dictionaries or instances of the dataclass itself.

## Stdlib dataclasses and _pydantic_ dataclasses

### Convert stdlib dataclasses into _pydantic_ dataclasses

Stdlib dataclasses (nested or not) can be easily converted into _pydantic_ dataclasses by just decorating
them with `pydantic.dataclasses.dataclass`.
_Pydantic_ will enhance the given stdlib dataclass but won't alter the default behaviour (i.e. without validation).
It will instead create a wrapper around it to trigger validation that will act like a plain proxy.
The stdlib dataclass can still be accessed via the `__dataclass__` attribute (see example below).

```py
{!.tmp_examples/dataclasses_stdlib_to_pydantic.py!}
```
_(This script is complete, it should run "as is")_

### Choose when to trigger validation

As soon as your stdlib dataclass has been decorated with _pydantic_ dataclass decorator, magic methods have been
added to validate input data. If you want, you can still keep using your dataclass and choose when to trigger it.

```py
{!.tmp_examples/dataclasses_stdlib_run_validation.py!}
```
_(This script is complete, it should run "as is")_

### Inherit from stdlib dataclasses

Stdlib dataclasses (nested or not) can also be inherited and _pydantic_ will automatically validate
all the inherited fields.

```py
{!.tmp_examples/dataclasses_stdlib_inheritance.py!}
```
_(This script is complete, it should run "as is")_

### Use of stdlib dataclasses with `BaseModel`

Bear in mind that stdlib dataclasses (nested or not) are **automatically converted** into _pydantic_
dataclasses when mixed with `BaseModel`! Furthermore the generated _pydantic_ dataclass will have
the **exact same configuration** (`order`, `frozen`, ...) as the original one.

```py
{!.tmp_examples/dataclasses_stdlib_with_basemodel.py!}
```
_(This script is complete, it should run "as is")_

### Use custom types

Since stdlib dataclasses are automatically converted to add validation using
custom types may cause some unexpected behaviour.
In this case you can simply add `arbitrary_types_allowed` in the config!

```py
{!.tmp_examples/dataclasses_arbitrary_types_allowed.py!}
```
_(This script is complete, it should run "as is")_

## Initialize hooks

When you initialize a dataclass, it is possible to execute code *after* validation
with the help of `__post_init_post_parse__`. This is not the same as `__post_init__`, which executes
code *before* validation.

!!! tip
    If you use a stdlib `dataclass`, you may only have `__post_init__` available and wish the validation to
    be done before. In this case you can set `Config.post_init_call = 'after_validation'`


```py
{!.tmp_examples/dataclasses_post_init_post_parse.py!}
```
_(This script is complete, it should run "as is")_

Since version **v1.0**, any fields annotated with `dataclasses.InitVar` are passed to both `__post_init__` *and*
`__post_init_post_parse__`.

```py
{!.tmp_examples/dataclasses_initvars.py!}
```
_(This script is complete, it should run "as is")_

### Difference with stdlib dataclasses

Note that the `dataclasses.dataclass` from Python stdlib implements only the `__post_init__` method since it doesn't run a validation step.

When substituting usage of `dataclasses.dataclass` with `pydantic.dataclasses.dataclass`, it is recommended to move the code executed in the `__post_init__` method to the `__post_init_post_parse__` method, and only leave behind part of code which needs to be executed before validation.

## JSON Dumping

_Pydantic_ dataclasses do not feature a `.json()` function. To dump them as JSON, you will need to make use of the `pydantic_encoder` as follows:

```py
{!.tmp_examples/dataclasses_json_dumps.py!}
```
