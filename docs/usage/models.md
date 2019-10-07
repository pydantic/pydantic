The primary means of defining objects in *pydantic* is via models 
(models are simply classes which inherit from `BaseModel`).

You can think of models as similar to types in strictly typed languages or the requirements of a single endpoint
in an API.

Untrusted data can be passed to a model, after parsing and validation *pydantic* guarantees that the fields
of the resultant model instance will conform to the field types defined on the model.

!!! note
    *pydantic* is primarily a parsing library, **not a validation library**.
    Validation is a means to an end - building a model which conforms to the types and constraints provided.

    In other words *pydantic* guarantees the types and constraints of the output model, not the input data.

    This might sound like an esoteric distinction, but it is not - you should read about 
    [Data Conversion](#data-conversion) if you're unsure what this means or how it might effect your usage.

## Basic model usage

```py
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name = 'Jane Doe'
```
`User` here is a model with two fields `id` which is an integer and is required, 
and `name` which is a string and is not required (it has a default value). The type of `name` is inferred from the
default value, thus a type annotation is not required (however note [this](#field-ordering) warning about field 
order when some fields do not have type annotations).
```py
user = User(id='123')
```
`user` here is an instance of `User`. Initialisation of the object will perform all parsing and validation,
if no `ValidationError` is raised, you know the resulting model instance is valid.
```py
assert user.id == 123
```
fields of a model can be accessed as normal attributes of the user object
the string '123' has been cast to an int as per the field type
```py
assert user.name == 'Jane Doe'
```
name wasn't set when user was initialised, so it has the default value
```py
assert user.__fields_set__ == {'id'}
```
the fields which were supplied when user was initialised:
```py
assert user.dict() == dict(user) == {'id': 123, 'name': 'Jane Doe'}
```
either `.dict()` or `dict(user)` will provide a dict of fields, but `.dict()` can take numerous other arguments.
```py
user.id = 321
assert user.id == 321
```
This model is mutable so field values can be changed.

### Model properties

The example above only shows the tip of the iceberg of what models can do. 
Models contains the following methods and attributes:

`dict()`
: returns a dictionary of the model's fields and values, 
  see [exporting models](exporting_models.md#modeldict) for more details

`json()`
: returns a JSON string representation `dict()`, 
  see [exporting models](exporting_models.md#modeljson) for more details

`copy()`
: returns a deep copy of the model, see [exporting models](exporting_models.md#modeldcopy) for more details

`parse_obj()`
: utility for loading any object into a model with error handling if the object is not a dictionary,
  see [helper function below](#helper-functions)

`parse_raw()`
: utility for loading strings of numerous formats, see [helper function below](#helper-functions)

`parse_file()`
: like `parse_raw()` but for files, see [helper function below](#helper-functions)

`from_orm()`
: for loading data from arbitrary classes, see [ORM mode below](#orm-mode-aka-arbitrary-class-instances)

`schema()`
: returns a dictionary representing the model as JSON Schema, see [Schema](schema.md)

`schema_json()`
: returns a JSON string representation `schema()`, see [Schema](schema.md)

`fields`
: a dictionary of the model class's fields

`__config__`
: the configuration class for this model, see [model config](model_config.md)

`__fields_set__`
: Set of names of fields which were set when the model instance was initialised

## Recursive Models

More complex hierarchical data structures can be defined using models as types in annotations themselves.

The ellipsis `...` just means "Required" same as annotation only declarations above.

```py
{!./examples/recursive.py!}
```
_(This script is complete, it should run "as is")_

For self-referencing models, see [postponed annotations](postponed_annotations.md#self-referencing-models).

## ORM Mode (aka Arbitrary Class Instances)

Pydantic models can be created from arbitrary class instances to support models that map to ORM objects.

To do this:
1. The [Config](model_config.md) property `orm_mode` must be set to `True`.
2. The special constructor `from_orm` must be used to create the model instance.

The example here uses SQLAlchemy but the same approach should work for any ORM.

```py
{!./examples/orm_mode.py!}
```
_(This script is complete, it should run "as is")_

ORM instances will be parsed with `from_orm` recursively as well as at the top level.

Here a vanilla class is used to demonstrate the principle, but any ORM could be used instead.

```py
{!./examples/orm_mode_recursive.py!}
```
_(This script is complete, it should run "as is")_

Arbitrary classes are processed by *pydantic* using the `GetterDict` class
(see [utils.py](https://github.com/samuelcolvin/pydantic/blob/master/pydantic/utils.py)) which attempts to
provide a dictionary-like interface to any class. You can customise how this works by setting your own
sub-class of `GetterDict` in `Config.getter_dict` (see [config](model_config.md)).

You can also customise class validation using [root_validators](validators.md#root-validators) with `pre=True`, 
in this case your validator function will be passed a `GetterDict` instance which you may copy and modify.

## Error Handling

*pydantic* will raise `ValidationError` whenever it finds an error in the data it's validating.

!!! note
    Validation code should not raise `ValidationError` itself, but rather raise `ValueError`, `TypeError` or
    `AssertionError` (or subclasses of `ValueError` or `TypeError`) which will be caught and used to populate
    `ValidationError`.

One exception will be raised regardless of the number of errors found, that `ValidationError` will
contain information about all the errors and how they happened.

You can access these errors in a several ways:

`e.errors()`
: method will return list of errors found in the input data.

`e.json()`
: method will return a JSON representation of `errors`.

`str(e)`
: method will return a human readable representation of the errors.

Each error object contains:

`loc`
: the error's location as a list, the first item in the list will be the field where the error occurred,
  subsequent items will represent the field where the error occurred
  in [sub models](models.md#recursive_models) when they're used.

`type`
: a unique identifier of the error readable by a computer.

`msg`
: a human readable explanation of the error.

`ctx`
: an optional object which contains values required to render the error message.

To demonstrate that:

```py
{!./examples/errors1.py!}
```
_(This script is complete, it should run "as is". `json()` has `indent=2` set by default, but I've tweaked the
JSON here and below to make it slightly more concise.)_

### Custom Errors

In your custom data types or validators you should use `ValueError`, `TypeError` or `AssertionError` to raise errors.

See [validators](validators.md) for more details on use of the `@validator` decorator.

```py
{!./examples/errors2.py!}
```
_(This script is complete, it should run "as is")_

You can also define your own error class with abilities to specify custom error code, message template and context:

```py
{!./examples/errors3.py!}
```
_(This script is complete, it should run "as is")_

## Helper Functions

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
_(This script is complete, it should run "as is")_

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
_(This script is complete, it should run "as is")_

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
a model. See [model config](model_config.md) for more details on `Config`.

!!! warning
    Immutability in python is never strict. If developers are determined/stupid they can always
    modify a so-called "immutable" object.

```py
{!./examples/mutation.py!}
```

Trying to change `a` caused an error and it remains unchanged, however the dict `b` is mutable and the
immutability of `foobar` doesn't stop `b` from being changed.

## Abstract Base Classes

Pydantic models can be used alongside Python's
[Abstract Base Classes](https://docs.python.org/3/library/abc.html) (ABCs).

```py
{!./examples/ex_abc.py!}
```
_(This script is complete, it should run "as is")_

## Field Ordering

Field order is important in models for the following reason:

* validation is performed in the order fields are defined; [fields validators](validators.md) 
  can access the values of earlier fields, but not later ones
* field order is preserved in the model [schema](schema.md)
* field order is preserved in [validation errors](#error-handling)
* field order is preserved by [`.dict()` and `.json()` etc.](exporting_models.md#modeldict)

As of **v1.0** all fields with annotations (both annotation only and annotations with a value) come first followed
by fields with no annotation. Within each group fields remain in the order they were defined.

```py
{!./examples/field_order.py!}
```
_(This script is complete, it should run "as is")_

!!! warning
    Note here that field order when both annotated and un-annotated fields are used is esoteric and not obvious
    at first glance.

    **In general therefore, it's preferable to add type annotations to all fields even when a default value
    also defines the type.**

## Required fields

In addition to annotation only fields to denote required fields, an ellipsis (`...`) can be used as the value

```py
from pydantic import BaseModel

class Model(BaseModel):
    a: int
    b: int = ...
```

Here both `a` and `b` are required here. Use of ellipses for required fields does not work well with [mypy](mypy.md)
so should generally be avoided.

## Data Conversion

*pydantic* may cast input data to force it to conform model field types. This may result in information being lost, take
the following example:

```py
{!./examples/data_conversion.py!}
```
_(This script is complete, it should run "as is")_

This is a deliberate decision of *pydantic*, and in general it's the most useful approach, see 
[here](https://github.com/samuelcolvin/pydantic/issues/578) for a longer discussion of the subject.
