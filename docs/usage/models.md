### Recursive Models

More complex hierarchical data structures can be defined using models as types in annotations themselves.

The ellipsis `...` just means "Required" same as annotation only declarations above.

```py
{!./examples/recursive.py!}
```

(This script is complete, it should run "as is")

For self-referencing models, see [postponed annotations](postponed_annotations.md#self-referencing-models).

### ORM Mode (aka Arbitrary Class Instances)

Pydantic models can be created from arbitrary class instances to support models that map to ORM objects.

To do this:
1. The [Config](model_config.md) property `orm_mode` must be set to `True`.
2. The special constructor `from_orm` must be used to create the model instance.

The example here uses SQLAlchemy but the same approach should work for any ORM.

```py
{!./examples/orm_mode.py!}
```

(This script is complete, it should run "as is")

ORM instances will be parsed with `from_orm` recursively as well as at the top level.

Here a vanilla class is used to demonstrate the principle, but any ORM could be used instead.

```py
{!./examples/orm_mode_recursive.py!}
```

(This script is complete, it should run "as is")

Arbitrary classes are processed by *pydantic* using the `GetterDict` class
(see [utils.py](https://github.com/samuelcolvin/pydantic/blob/master/pydantic/utils.py)) which attempts to
provide a dictionary-like interface to any class. You can customise how this works by setting your own
sub-class of `GetterDict` in `Config.getter_dict` (see [config](model_config.md)).

You can also customise class validation using [root_validators](validators.md#root-validators) with `pre=True`, in this case
your validator function will be passed a `GetterDict` instance which you may copy and modify.

### Helper Functions

*Pydantic* provides three `classmethod` helper functions on models for parsing data:

* **`parse_obj`** this is almost identical to the `__init__` method of the model except if the object passed is not
  a dict `ValidationError` will be raised (rather than python raising a `TypeError`).
* **`parse_raw`** takes a *str* or *bytes* parses it as *json*, or *pickle* data and then passes
  the result to `parse_obj`. The data type is inferred from the `content_type` argument,
  otherwise *json* is assumed.
* **`parse_file`** reads a file and passes the contents to `parse_raw`, if `content_type` is omitted it is inferred
  from the file's extension.

```py
{!./examples/parse.py!}
```

(This script is complete, it should run "as is")

!!! note
    Since `pickle` allows complex objects to be encoded, to use it you need to explicitly pass `allow_pickle` to
    the parsing function.

## Generic Models

!!! note
    New in version **v0.29**.

    This feature requires Python 3.7+.

Pydantic supports the creation of generic models to make it easier to reuse a common model structure.

In order to declare a generic model, you perform the following steps:

* Declare one or more `typing.TypeVar` instances to use to parameterize your model.
* Declare a pydantic model that inherits from `pydantic.generics.GenericModel` and `typing.Generic`,
  where you pass the `TypeVar` instances as parameters to `typing.Generic`.
* Use the `TypeVar` instances as annotations where you will want to replace them with other types or
  pydantic models.

Here is an example using `GenericModel` to create an easily-reused HTTP response payload wrapper:

```py
{!./examples/generics.py!}
```

(This script is complete, it should run "as is")

If you set `Config` or make use of `validator` in your generic model definition, it is applied
to concrete subclasses in the same way as when inheriting from `BaseModel`. Any methods defined on
your generic class will also be inherited.

Pydantic's generics also integrate properly with mypy, so you get all the type checking
you would expect mypy to provide if you were to declare the type without using `GenericModel`.

!!! note
    Internally, pydantic uses `create_model` to generate a (cached) concrete `BaseModel` at runtime,
    so there is essentially zero overhead introduced by making use of `GenericModel`.

## Dynamic model creation

There are some occasions where the shape of a model is not known until runtime, for this *pydantic* provides
the `create_model` method to allow models to be created on the fly.

```py
{!./examples/dynamic_model_creation.py!}
```

Here `StaticFoobarModel` and `DynamicFoobarModel` are identical.

Fields are defined by either a a tuple of the form `(<type>, <default value>)` or just a default value. The
special key word arguments `__config__` and `__base__` can be used to customise the new model. This includes
extending a base model with extra fields.

```py
{!./examples/dynamic_inheritance.py!}
```

## Custom Root Types

Pydantic models which do not represent a `dict` ("object" in JSON parlance) can have a custom
root type defined via the `__root__` field. The root type can of any type: list, float, int etc.

The root type can be defined via the type hint on the `__root__` field.
The root value can be passed to model `__init__` via the `__root__` keyword argument or as
the first and only argument to `parse_obj`.

```py
{!examples/custom_root_field.py!}
```

## Faux Immutability

Models can be configured to be immutable via `allow_mutation = False` this will prevent changing attributes of
a model.

!!! warning
    Immutability in python is never strict. If developers are determined/stupid they can always
    modify a so-called "immutable" object.

```py
{!./examples/mutation.py!}
```

Trying to change `a` caused an error and it remains unchanged, however the dict `b` is mutable and the
immutability of `foobar` doesn't stop being changed.

## Abstract Base Classes

Pydantic models can be used alongside Python's
[Abstract Base Classes](https://docs.python.org/3/library/abc.html) (ABCs).

```py
{!./examples/ex_abc.py!}
```

(This script is complete, it should run "as is")
