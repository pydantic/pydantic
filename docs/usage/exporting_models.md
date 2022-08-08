As well as accessing model attributes directly via their names (e.g. `model.foobar`), models can be converted
and exported in a number of ways:

## `model.dict(...)`

This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-and-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-and-exclude)
* `by_alias`: whether field aliases should be used as keys in the returned dictionary; default `False`
* `exclude_unset`: whether fields which were not explicitly set when creating the model should
  be excluded from the returned dictionary; default `False`.
  Prior to **v1.0**, `exclude_unset` was known as `skip_defaults`; use of `skip_defaults` is now deprecated
* `exclude_defaults`: whether fields which are equal to their default values (whether set or otherwise) should
  be excluded from the returned dictionary; default `False`
* `exclude_none`: whether fields which are equal to `None` should be excluded from the returned dictionary; default
  `False`

Example:

```py
{!.tmp_examples/exporting_models_dict.py!}
```
_(This script is complete, it should run "as is")_

## `dict(model)` and iteration

*pydantic* models can also be converted to dictionaries using `dict(model)`, and you can also
iterate over a model's field using `for field_name, value in model:`. With this approach the raw field values are
returned, so sub-models will not be converted to dictionaries.

Example:

```py
{!.tmp_examples/exporting_models_iterate.py!}
```
_(This script is complete, it should run "as is")_

## `model.copy(...)`

`copy()` allows models to be duplicated, which is particularly useful for immutable models.

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-and-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-and-exclude)
* `update`: a dictionary of values to change when creating the copied model
* `deep`: whether to make a deep copy of the new model; default `False`

Example:

```py
{!.tmp_examples/exporting_models_copy.py!}
```
_(This script is complete, it should run "as is")_

## `model.json(...)`

The `.json()` method will serialise a model to JSON. Typically, `.json()` in turn calls `.dict()` and
serialises its result. (For models with a [custom root type](models.md#custom-root-types), after calling `.dict()`,
only the value for the `__root__` key is serialised)

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-and-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-and-exclude)
* `by_alias`: whether field aliases should be used as keys in the returned dictionary; default `False`
* `exclude_unset`: whether fields which were not set when creating the model and have their default values should
  be excluded from the returned dictionary; default `False`.
  Prior to **v1.0**, `exclude_unset` was known as `skip_defaults`; use of `skip_defaults` is now deprecated
* `exclude_defaults`: whether fields which are equal to their default values (whether set or otherwise) should
  be excluded from the returned dictionary; default `False`
* `exclude_none`: whether fields which are equal to `None` should be excluded from the returned dictionary; default
  `False`
* `encoder`: a custom encoder function passed to the `default` argument of `json.dumps()`; defaults to a custom
  encoder designed to take care of all common types
* `**dumps_kwargs`: any other keyword arguments are passed to `json.dumps()`, e.g. `indent`.

*pydantic* can serialise many commonly used types to JSON (e.g. `datetime`, `date` or `UUID`) which would normally
fail with a simple `json.dumps(foobar)`.

```py
{!.tmp_examples/exporting_models_json.py!}
```
_(This script is complete, it should run "as is")_

### `json_encoders`

Serialisation can be customised on a model using the `json_encoders` config property; the keys should be types (or names of types for forward references), and
the values should be functions which serialise that type (see the example below):

```py
{!.tmp_examples/exporting_models_json_encoders.py!}
```
_(This script is complete, it should run "as is")_

By default, `timedelta` is encoded as a simple float of total seconds. The `timedelta_isoformat` is provided
as an optional alternative which implements [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) time diff encoding.

The `json_encoders` are also merged during the models inheritance with the child
encoders taking precedence over the parent one.

```py
{!.tmp_examples/exporting_models_json_encoders_merge.py!}
```
_(This script is complete, it should run "as is")_

### Serialising self-reference or other models

By default, models are serialised as dictionaries.
If you want to serialise them differently, you can add `models_as_dict=False` when calling `json()` method
and add the classes of the model in `json_encoders`.
In case of forward references, you can use a string with the class name instead of the class itself
```py
{!.tmp_examples/exporting_models_json_forward_ref.py!}
```
_(This script is complete, it should run "as is")_

### Nested serialisation of other models

By default, models that contain other models are serialised using the `json_encoders` functions of the
parent or container class.
However, you may want to nest classes in a modular fashion, including their `json_encoders`.
In this case, call `json(use_nested_encoders=True)`.
`use_nested_encoders` has no effect when `models_as_dict=False`, as the classes of the models
are expected to be defined in the top-level `json_encoders`.

```py
{!.tmp_examples/exporting_models_json_nested_encoders.py!}
```
_(This script is complete, it should run "as is")_

### Serialising subclasses

!!! note
    New in version **v1.5**.

    Subclasses of common types were not automatically serialised to JSON before **v1.5**.

Subclasses of common types are automatically encoded like their super-classes:

```py
{!.tmp_examples/exporting_models_json_subclass.py!}
```
_(This script is complete, it should run "as is")_

### Custom JSON (de)serialisation

To improve the performance of encoding and decoding JSON, alternative JSON implementations
(e.g. [ujson](https://pypi.python.org/pypi/ujson)) can be used via the
`json_loads` and `json_dumps` properties of `Config`.

```py
{!.tmp_examples/exporting_models_ujson.py!}
```
_(This script is complete, it should run "as is")_

`ujson` generally cannot be used to dump JSON since it doesn't support encoding of objects like datetimes and does
not accept a `default` fallback function argument. To do this, you may use another library like
[orjson](https://github.com/ijl/orjson).

```py
{!.tmp_examples/exporting_models_orjson.py!}
```
_(This script is complete, it should run "as is")_

Note that `orjson` takes care of `datetime` encoding natively, making it faster than `json.dumps` but
meaning you cannot always customise the encoding using `Config.json_encoders`.

## `pickle.dumps(model)`

Using the same plumbing as `copy()`, *pydantic* models support efficient pickling and unpickling.

```py
{!.tmp_examples/exporting_models_pickle.py!}
```
_(This script is complete, it should run "as is")_

## Advanced include and exclude

The `dict`, `json`, and `copy` methods support `include` and `exclude` arguments which can either be
sets or dictionaries. This allows nested selection of which fields to export:

```py
{!.tmp_examples/exporting_models_exclude1.py!}
```

The `True` indicates that we want to exclude or include an entire key, just as if we included it in a set.
Of course, the same can be done at any depth level.

Special care must be taken when including or excluding fields from a list or tuple of submodels or dictionaries.  In this scenario,
`dict` and related methods expect integer keys for element-wise inclusion or exclusion. To exclude a field from **every**
member of a list or tuple, the dictionary key `'__all__'` can be used as follows:

```py
{!.tmp_examples/exporting_models_exclude2.py!}
```

The same holds for the `json` and `copy` methods.

### Model and field level include and exclude

In addition to the explicit arguments `exclude` and `include` passed to `dict`, `json` and `copy` methods, we can also pass the `include`/`exclude` arguments directly to the `Field` constructor or the equivalent `field` entry in the models `Config` class:

```py
{!.tmp_examples/exporting_models_exclude3.py!}
```

In the case where multiple strategies are used, `exclude`/`include` fields are merged according to the following rules:

* First, model config level settings (via `"fields"` entry) are merged per field with the field constructor settings (i.e. `Field(..., exclude=True)`), with the field constructor taking priority.
* The resulting settings are merged per class with the explicit settings on `dict`, `json`, `copy` calls with the explicit settings taking priority.

Note that while merging settings, `exclude` entries are merged by computing the "union" of keys, while `include` entries are merged by computing the "intersection" of keys.

The resulting merged exclude settings:

```py
{!.tmp_examples/exporting_models_exclude4.py!}
```

are the same as using merged include settings as follows:

```py
{!.tmp_examples/exporting_models_exclude5.py!}
```
