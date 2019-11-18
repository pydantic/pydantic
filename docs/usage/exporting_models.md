As well as accessing model attributes directly via their names (e.g. `model.foobar`), models can be converted
and exported in a number of ways:

## `model.dict(...)`

This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-exclude)
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

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-exclude)
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
only the value for the `__root__` key is serialised.)

Serialisation can be customised on a model using the `json_encoders` config property; the keys should be types, and
the values should be functions which serialise that type (see the example below).

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-exclude)
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

Example:

```py
{!.tmp_examples/exporting_models_json.py!}
```
_(This script is complete, it should run "as is")_

By default, `timedelta` is encoded as a simple float of total seconds. The `timedelta_isoformat` is provided
as an optional alternative which implements ISO 8601 time diff encoding.

See [below](#custom-json-deserialisation) for details on how to use other libraries for more performant JSON encoding
and decoding.

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

The ellipsis (``...``) indicates that we want to exclude or include an entire key, just as if we included it in a set.
Of course, the same can be done at any depth level:

```py
{!.tmp_examples/exporting_models_exclude2.py!}
```

The same holds for the `json` and `copy` methods.

## Custom JSON (de)serialisation

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
