If you don't want to use pydantic's `BaseModel` you can instead get the same data validation on standard
[dataclasses](https://docs.python.org/3/library/dataclasses.html) (introduced in python 3.7).

Dataclasses work in python 3.6 using the [dataclasses backport package](https://github.com/ericvsmith/dataclasses).

```py
{!.tmp_examples/dataclasses_main.py!}
```
_(This script is complete, it should run "as is")_

!!! note
    Keep in mind that `pydantic.dataclasses.dataclass` is a drop-in replacement for `dataclasses.dataclass`
    with validation, **not** a replacement for `pydantic.BaseModel`. There are cases where subclassing
    `pydantic.BaseModel` is the better choice. 
    
    For more information and discussion see
    [samuelcolvin/pydantic#710](https://github.com/samuelcolvin/pydantic/issues/710).

You can use all the standard pydantic field types, and the resulting dataclass will be identical to the one
created by the standard library `dataclass` decorator.

The underlying model and its schema can be accessed through `__pydantic_model__`.
Also, fields that require a `default_factory` can be specified by a `dataclasses.field`.

```py
{!.tmp_examples/dataclasses_default_schema.py!}
```
_(This script is complete, it should run "as is")_

`pydantic.dataclasses.dataclass`'s arguments are the same as the standard decorator, except one extra
keyword argument `config` which has the same meaning as [Config](model_config.md).

!!! note
    As a side effect of getting pydantic dataclasses to play nicely with mypy, the `config` argument will show
    as invalid in IDEs and mypy. Use `@dataclass(..., config=Config) # type: ignore` as a workaround. 

    See [python/mypy#6239](https://github.com/python/mypy/issues/6239) for an explanation of this issue.

For more information about combining validators with dataclasses, see 
[dataclass validators](validators.md#dataclass-validators).

## Nested dataclasses

Nested dataclasses are supported both in dataclasses and normal models.

```py
{!.tmp_examples/dataclasses_nested.py!}
```
_(This script is complete, it should run "as is")_

Dataclasses attributes can be populated by tuples, dictionaries or instances of the dataclass itself.

## Initialize hooks

When you initialize a dataclass, it is possible to execute code *after* validation
with the help of `__post_init_post_parse__`. This is not the same as `__post_init__`, which executes
code *before* validation.

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
