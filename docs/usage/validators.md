Custom validation and complex relationships between objects can be achieved using the `validator` decorator.

```py
{!./examples/validators_simple.py!}
```

_(This script is complete, it should run "as is")_

A few things to note on validators:

* validators are "class methods", the first value they receive here will be the `UserModel` not an instance
  of `UserModel`
* their signature can be `(cls, value)` or `(cls, value, values, config, field)`. Any subset of
  `values`, `config` and `field` is also permitted, eg. `(cls, value, field)`, however due to the way
  validators are inspected, the variadic key word argument ("``**kwargs``") **must** be called `kwargs`.
* validators should either return the new value or raise a `ValueError`, `TypeError`, or `AssertionError`
  (``assert`` statements may be used).

!!! warning
    If you make use of `assert` statements, keep in mind that running
    Python with the [`-O` optimization flag](https://docs.python.org/3/using/cmdline.html#cmdoption-o)
    disables `assert` statements, and **validators will stop working**.

* where validators rely on other values, you should be aware that:

  - Validation is done in the order fields are defined, eg. here `password2` has access to `password1`
    (and `name`), but `password1` does not have access to `password2`. You should heed the warning in
    [mypy usage ](mypy.md) regarding field order and required fields.

  - If validation fails on another field (or that field is missing) it will not be included in `values`, hence
    `if 'password1' in values and ...` in this example.

!!! warning
    Be aware that mixing annotated and non-annotated fields may alter the order of your fields in metadata and errors,
    and for validation: annotated fields will always come before non-annotated fields.
    (Within each group fields remain in the order they were defined.)

## Pre and per-item validators

Validators can do a few more complex things:

```py
{!./examples/validators_pre_item.py!}
```

_(This script is complete, it should run "as is")_

A few more things to note:

* a single validator can apply to multiple fields, either by defining multiple fields or by the special value `'*'`
  which means that validator will be called for all fields.
* the keyword argument `pre` will cause validators to be called prior to other validation
* the `each_item` keyword argument will mean validators are applied to individual values
  (eg. of `List`, `Dict`, `Set` etc.) not the whole object

## Validate Always

For performance reasons by default validators are not called for fields where the value is not supplied.
However there are situations where it's useful or required to always call the validator, e.g.
to set a dynamic default value.

```py
{!./examples/validators_always.py!}
```

_(This script is complete, it should run "as is")_

You'll often want to use this together with `pre` since otherwise with `always=True`
*pydantic* would try to validate the default `None` which would cause an error.

## Root Validators

Validation can also be performed on the entire model's data.

```py
{!./examples/validators_root.py!}
```

_(This script is complete, it should run "as is")_

As with field validators, root validators can be `pre=True` in which case they're called before field
validation occurs with the raw input data, or `pre=False` (the default) in which case
they're called after field validation.

Field validation will not occur if "pre" root validators raise an error. As with field validators,
"post" (e.g. non `pre`) root validators will be called even if field validation fails; the `values` argument will
be a dict containing the values which passed field validation and field defaults where applicable.

## Field Checks

On class creation validators are checked to confirm that the fields they specify actually exist on the model.

Occasionally however this is not wanted: when you define a validator to validate fields on inheriting models.
In this case you should set `check_fields=False` on the validator.

## Dataclass Validators

Validators also work in Dataclasses.

```py
{!./examples/validators_dataclass.py!}
```

_(This script is complete, it should run "as is")_
