### PEP 484 Types

*pydantic* uses `typing` types to define more complex objects.

```py
{!./examples/ex_typing.py!}
```

(This script is complete, it should run "as is")

### dataclasses

!!! note
    New in version `v0.14`.

If you don't want to use pydantic's `BaseModel` you can instead get the same data validation on standard
[dataclasses](https://docs.python.org/3/library/dataclasses.html) (introduced in python 3.7).

Dataclasses work in python 3.6 using the [dataclasses backport package](https://github.com/ericvsmith/dataclasses).

```py
{!./examples/ex_dataclasses.py!}
```

(This script is complete, it should run "as is")

!!! note
    Keep in mind that `pydantic.dataclasses.dataclass` is a drop in replacement for `dataclasses.dataclass`
    with validation, not a repacement for `pydantic.BaseModel`. There are cases where subclassing
    `pydantic.BaseModel` is the better choice. For more information and disucssion see
    [samuelcolvin/pydantic#6239](https://github.com/samuelcolvin/pydantic/issues/710).

You can use all the standard pydantic field types and the resulting dataclass will be identical to the one
created by the standard library `dataclass` decorator.

`pydantic.dataclasses.dataclass`'s arguments are the same as the standard decorator, except one extra
key word argument `config` which has the same meaning as [Config](usage.md#config).

!!! note
    As a side effect of getting pydantic dataclasses to play nicely with mypy the `config` argument will show
    as invalid in IDEs and mypy, use `@dataclass(..., config=Config) # type: ignore` as a workaround. See
    [python/mypy#6239](https://github.com/python/mypy/issues/6239) for an explanation of why this is.

#### Nested dataclasses

Since version `v0.17` nested dataclasses are supported both in dataclasses and normal models.

```py
{!./examples/ex_nested_dataclasses.py!}
```

(This script is complete, it should run "as is")

Dataclasses attributes can be populated by tuples, dictionaries or instances of that dataclass.

#### Initialize hooks

Since version `v0.28` when you initialize a dataclass, it is possible to execute code after validation
with the help of `__post_init_post_parse__`. This is not the same as `__post_init__` which executes
code before validation.

```py
{!./examples/ex_post_init_post_parse.py!}
```

(This script is complete, it should run “as is”)

Since version `v1.0`, any fields annotated with `dataclasses.InitVar` are passed to both `__post_init__` *and*
`__post_init_post_parse__`.

```py
{!./examples/ex_post_init_post_parse_initvars.py!}
```

(This script is complete, it should run “as is”)

### Choices

*pydantic* uses python's standard `enum` classes to define choices.

```py
{!./examples/choices.py!}
```

(This script is complete, it should run "as is")

### Validators

Custom validation and complex relationships between objects can achieved using the `validator` decorator.

```py
{!./examples/validators_simple.py!}
```

(This script is complete, it should run "as is")

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
    Python with the [`-O`` `optimization flag](https://docs.python.org/3/using/cmdline.html#cmdoption-o)
    disables `assert` statements, and **validators will stop working**.

* where validators rely on other values, you should be aware that:

  - Validation is done in the order fields are defined, eg. here `password2` has access to `password1`
    (and `name`), but `password1` does not have access to `password2`. You should heed the warning
    [below](usage.md#usage_mypy_required) regarding field order and required fields.

  - If validation fails on another field (or that field is missing) it will not be included in `values`, hence
    `if 'password1' in values and ...` in this example.

!!! warning
    Be aware that mixing annotated and non-annotated fields may alter the order of your fields in metadata and errors,
    and for validation: annotated fields will always come before non-annotated fields.
    (Within each group fields remain in the order they were defined.)

#### Pre and per-item validators

Validators can do a few more complex things:

```py
{!./examples/validators_pre_item.py!}
```

(This script is complete, it should run "as is")

A few more things to note:

* a single validator can apply to multiple fields, either by defining multiple fields or by the special value `'*'`
  which means that validator will be called for all fields.
* the keyword argument `pre` will cause validators to be called prior to other validation
* the `each_item` keyword argument will mean validators are applied to individual values
  (eg. of `List`, `Dict`, `Set` etc.) not the whole object

#### Validate Always

For performance reasons by default validators are not called for fields where the value is not supplied.
However there are situations where it's useful or required to always call the validator, e.g.
to set a dynamic default value.

```py
{!./examples/validators_always.py!}
```

(This script is complete, it should run "as is")

You'll often want to use this together with `pre` since otherwise with `always=True`
*pydantic* would try to validate the default `None` which would cause an error.

#### Root Validators

Validation can also be performed on the entire model's data.

```py
{!./examples/validators_root.py!}
```

(This script is complete, it should run "as is")

As with field validators, root validators can be `pre=True` in which case they're called before field
validation occurs with the raw input data, or `pre=False` (the default) in which case
they're called after field validation.

Field validation will not occur if "pre" root validators raise an error. As with field validators,
"post" (e.g. non `pre`) root validators will be called even if field validation fails; the `values` argument will
be a dict containing the values which passed field validation and field defaults where applicable.

#### Dataclass Validators

Validators also work in Dataclasses.

```py
{!./examples/validators_dataclass.py!}
```

(This script is complete, it should run "as is")

#### Field Checks

On class creation validators are checked to confirm that the fields they specify actually exist on the model.

Occasionally however this is not wanted: when you define a validator to validate fields on inheriting models.
In this case you should set `check_fields=False` on the validator.

### Recursive Models

More complex hierarchical data structures can be defined using models as types in annotations themselves.

The ellipsis `...` just means "Required" same as annotation only declarations above.

```py
{!./examples/recursive.py!}
```

(This script is complete, it should run "as is")

#### Self-referencing Models

Data structures with self-referencing models are also supported, provided the function
`update_forward_refs()` is called once the model is created (you will be reminded
with a friendly error message if you don't).

Within the model, you can refer to the not-yet-constructed model by a string :

```py
{!./examples/self_referencing_string.py!}
```

(This script is complete, it should run "as is")

Since `python 3.7`, You can also refer it by its type, provided you import `annotations` (see
[the relevant paragraph](usage.md#postponed_annotations) for support depending on Python
and pydantic versions).

```py
{!./examples/self_referencing_annotations.py!}
```

(This script is complete, it should run "as is")

### Generic Models

!!! note
    New in version v0.29.

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

### ORM Mode (aka Arbitrary Class Instances)

Pydantic models can be created from arbitrary class instances to support models that map to ORM objects.

To do this:
1. The [Config](usage.md#config) property `orm_mode` must be set to `True`.
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
(see [utils.py](https://github.com/samuelcolvin/pydantic/blob/master/pydantic/utils.py)_) which attempts to
provide a dictionary-like interface to any class. You can customise how this works by setting your own
sub-class of `GetterDict` in `Config.getter_dict` (see [config](usage.md#config)).

You can also customise class validation using [root_validators](usage.md#root_validators) with `pre=True`, in this case
your validator function will be passed a `GetterDict` instance which you may copy and modify.

### Schema Creation

*Pydantic* allows auto creation of JSON Schemas from models:

```py
{!./examples/schema1.py!}
```

(This script is complete, it should run "as is")

Outputs:

```json
{!./examples/schema1.json!}
```

The generated schemas are compliant with the specifications:
[JSON Schema Core](https://json-schema.org/latest/json-schema-core.html)_,
[JSON Schema Validation](https://json-schema.org/latest/json-schema-validation.html)_ and
[OpenAPI](https://github.com/OAI/OpenAPI-Specification)_.

`BaseModel.schema` will return a dict of the schema, while `BaseModel.schema_json` will return a JSON string
representation of that.

Sub-models used are added to the `definitions` JSON attribute and referenced, as per the spec.

All sub-models (and their sub-models) schemas are put directly in a top-level `definitions` JSON key for easy re-use
and reference.

"sub-models" with modifications (via the `Field` class) like a custom title, description or default value,
are recursively included instead of referenced.

The `description` for models is taken from the docstring of the class or the argument `description` to
the `Field` class.

Optionally the `Field` class can be used to provide extra information about the field and validations, arguments:

* `default` (positional argument), since the `Field` is replacing the field's default, its first
  argument is used to set the default, use ellipsis (``...``) to indicate the field is required
* `alias` - the public name of the field
* `title` if omitted `field_name.title()` is used
* `description` if omitted and the annotation is a sub-model, the docstring of the sub-model will be used
* `const` this field *must* take it's default value if it is present
* `gt` for numeric values (``int``, `float`, `Decimal`), adds a validation of "greater than" and an annotation
  of `exclusiveMinimum` to the JSON Schema
* `ge` for numeric values, adds a validation of "greater than or equal" and an annotation of `minimum` to the
  JSON Schema
* `lt` for numeric values, adds a validation of "less than" and an annotation of `exclusiveMaximum` to the
  JSON Schema
* `le` for numeric values, adds a validation of "less than or equal" and an annotation of `maximum` to the
  JSON Schema
* `multiple_of` for numeric values, adds a validation of "a multiple of" and an annotation of `multipleOf` to the
  JSON Schema
* `min_items` for list values, adds a corresponding validation and an annotation of `minItems` to the
  JSON Schema
* `max_items` for list values, adds a corresponding validation and an annotation of `maxItems` to the
  JSON Schema
* `min_length` for string values, adds a corresponding validation and an annotation of `minLength` to the
  JSON Schema
* `max_length` for string values, adds a corresponding validation and an annotation of `maxLength` to the
  JSON Schema
* `regex` for string values, adds a Regular Expression validation generated from the passed string and an
  annotation of `pattern` to the JSON Schema
* `**` any other keyword arguments (eg. `examples`) will be added verbatim to the field's schema

Instead of using `Field`, the `fields` property of [the Config class](usage.md#config) can be used
to set all the arguments above except `default`.

The schema is generated by default using aliases as keys, it can also be generated using model
property names not aliases with `MainModel.schema/schema_json(by_alias=False)`.

Types, custom field types, and constraints (as `max_length`) are mapped to the corresponding
[JSON Schema Core](http://json-schema.org/latest/json-schema-core.html#rfc.section.4.3.1)_ spec format when there's
an equivalent available, next to [JSON Schema Validation](http://json-schema.org/latest/json-schema-validation.html)_,
[OpenAPI Data Types](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types)_
(which are based on JSON Schema), or otherwise use the standard `format` JSON field to define Pydantic extensions
for more complex `string` sub-types.

The field schema mapping from Python / Pydantic to JSON Schema is done as follows:

.. include: .tmp_schema_mappings.rst

You can also generate a top-level JSON Schema that only includes a list of models and all their related
submodules in its `definitions`:

```py
{!./examples/schema2.py!}
```

(This script is complete, it should run "as is")

Outputs:

```py
{!./examples/schema2.json!}
```

You can customize the generated `$ref` JSON location, the definitions will still be in the key `definitions` and
you can still get them from there, but the references will point to your defined prefix instead of the default.

This is useful if you need to extend or modify JSON Schema default definitions location, e.g. with OpenAPI:

```py
{!./examples/schema3.py!}
```

(This script is complete, it should run "as is")

Outputs:

```py
{!./examples/schema3.json!}
```

It's also possible to extend/override the generated JSON schema in a model.

To do it, use the `Config` sub-class attribute `schema_extra`.

For example, you could add `examples` to the JSON Schema:

```py
{!./examples/schema4.py!}
```

(This script is complete, it should run "as is")

Outputs:

```py
{!./examples/schema4.json!}
```

### Error Handling

*Pydantic* will raise `ValidationError` whenever it finds an error in the data it's validating.

!!! note
    Validation code should not raise `ValidationError` itself, but rather raise `ValueError` or `TypeError`
    (or subclasses thereof) which will be caught and used to populate `ValidationError`.

One exception will be raised regardless of the number of errors found, that `ValidationError` will
contain information about all the errors and how they happened.

You can access these errors in a several ways:

* **`e.errors()`** method will return list of errors found in the input data.
* **`e.json()`** method will return a JSON representation of `errors`.
* **`str(e)`** method will return a human readable representation of the errors.

Each error object contains:

* **`loc`** the error's location as a list, the first item in the list will be the field where the error occurred,
 subsequent items will represent the field where the error occurred
 in [sub models](usage.md#recursive_models) when they're used.
* **`type`** a unique identifier of the error readable by a computer.
* **`msg`** a human readable explanation of the error.
* **`ctx`** an optional object which contains values required to render the error message.

To demonstrate that:

```py
{!./examples/errors1.py!}
```

(This script is complete, it should run "as is". `json()` has `indent=2` set by default, but I've tweaked the
JSON here and below to make it slightly more concise.)

In your custom data types or validators you should use `TypeError` and `ValueError` to raise errors:

```py
{!./examples/errors2.py!}
```

(This script is complete, it should run "as is")

You can also define your own error class with abilities to specify custom error code, message template and context:

```py
{!./examples/errors3.py!}
```

(This script is complete, it should run "as is")

### datetime Types

*Pydantic* supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)_
types:

* `datetime` fields can be:

  * `datetime`, existing `datetime` object
  * `int` or `float`, assumed as Unix time, e.g. seconds (if <= `2e10`) or milliseconds (if > `2e10`) since 1 January 1970
  * `str`, following formats work:

    * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z[±]HH[:]MM]]]`
    * `int` or `float` as a string (assumed as Unix time)

* `date` fields can be:

  * `date`, existing `date` object
  * `int` or `float`, see `datetime`
  * `str`, following formats work:

    * `YYYY-MM-DD`
    * `int` or `float`, see `datetime`

* `time` fields can be:

  * `time`, existing `time` object
  * `str`, following formats work:

    * `HH:MM[:SS[.ffffff]]`

* `timedelta` fields can be:

  * `timedelta`, existing `timedelta` object
  * `int` or `float`, assumed as seconds
  * `str`, following formats work:

    * `[-][DD ][HH:MM]SS[.ffffff]`
    * `[±]P[DD]DT[HH]H[MM]M[SS]S` (ISO 8601 format for timedelta)

```py
{!./examples/datetime_example.py!}
```

### Exotic Types

*Pydantic* comes with a number of utilities for parsing or validating common objects.

```py
{!./examples/exotic.py!}
```

(This script is complete, it should run "as is")

#### Booleans

!!! warning
    The logic for parsing `bool` fields has changed as of version v1.
    Prior to v1, `bool` parsing never failed, leading to some unexpected results.
    The new logic is described below.

A standard `bool` field will raise a `ValidationError` if the value is not one of the following:

* A valid boolean (i.e., `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of
  `'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid (per the previous rule) when decoded to `str`

Here is a script demonstrating some of these behaviors:

```py
{!./examples/boolean.py!}
```

(This script is complete, it should run "as is")

#### Callable

Fields can also be of type `Callable`:

```py
{!./examples/callable.py!}
```

(This script is complete, it should run "as is")

!!! warning
    Callable fields only perform a simple check that the argument is
    callable, no validation of arguments, their types or the return
    type is performed.

URLs
....

For URI/URL validation the following types are available:

- `AnyUrl`: any scheme allowed, TLD not required
- `AnyHttpUrl`: schema `http` or `https`, TLD not required
- `HttpUrl`: schema `http` or `https`, TLD required, max length 2083
- `PostgresDsn`: schema `postgres` or `postgresql`, userinfo required, TLD not required
- `RedisDsn`: schema `redis`, userinfo required, tld not required
- `stricturl`, method with the following keyword arguments:

  - `strip_whitespace: bool = True`
  - `min_length: int = 1`
  - `max_length: int = 2 ** 16`
  - `tld_required: bool = True`
  - `allowed_schemes: Optional[Set[str]] = None`

If you require custom types they can be created in a similar way to the application specific types defined above.

The above types (which all inherit from `AnyUrl`) will attempt to give descriptive errors when invalid URLs are
provided:

```py
{!./examples/urls.py!}
```

(This script is complete, it should run "as is")

#### URL Properties

Assuming an input URL of `http://samuel:pass@example.com:8000/the/path/?query=here#fragment=is;this=bit`,
the above types export the following properties:

- `scheme`: always set - the url schema e.g. `http` above
- `host`: always set - the url host e.g. `example.com` above
- `host_type`: always set - describes the type of host, either:

  - `domain`: e.g. for `example.com`,
  - `int_domain`: international domain, see [below](usage.md#int_domains), e.g. for `exampl£e.org`,
  - `ipv4`: an IP V4 address, e.g. for `127.0.0.1`, or
  - `ipv6`: an IP V6 address, e.g. for `2001:db8:ff00:42`

- `user`: optional - the username if included e.g. `samuel` above
- `password`: optional - the password if included e.g. `pass` above
- `tld`: optional - the top level domain e.g. `com` above,
  **Note: this will be wrong for any two level domain e.g. "co.uk".** You'll need to implement your own list of TLDs
  if you require full TLD validation
- `port`: optional - the port e.g. `8000` above
- `path`: optional - the path e.g. `/the/path/` above
- `query`: optional - the URL query (aka GET arguments or "search string") e.g. `query=here` above
- `fragment`: optional - the fragment e.g. `fragment=is;this=bit` above

If further validation is required, these properties can be used by validators to enforce specific behaviour:

```py
{!./examples/url_properties.py!}
```

(This script is complete, it should run "as is")

#### International Domains

"International domains" (e.g. a URL where the host includes non-ascii characters) will be encode via
[punycode](https://en.wikipedia.org/wiki/Punycode) (see
[this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```py
{!./examples/url_punycode.py!}
```

(This script is complete, it should run "as is")

#### Underscores in Hostnames

!!! note
    In *pydantic* underscores are allowed in all parts of a domain except the tld.
    Technically this might be wrong - in theory the hostname cannot have underscores but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk` hostname is `exam_ple`, should not be allowed as there's an underscore in there
    - `foo_bar.example.com` hostname is `example` should be allowed since the underscore is in the subdomain

    Without having an exhaustive list of TLDs it would be impossible to differentiate between these two. Therefore
    underscores are allowed, you could do further validation in a validator if you wanted.

    Also, chrome currently accepts `http://exam_ple.com` as a URL, so we're in good (or at least big) company.

### Color Type

You can use the `Color` data type for storing colors as per
[CSS3 specification](http://www.w3.org/TR/css3-color/#svg-color). Color can be defined via:

- [name](http://www.w3.org/TR/SVG11/types.html#ColorKeywords) (e.g. `"Black"`, `"azure"`)
- [hexadecimal value](https://en.wikipedia.org/wiki/Web_colors#Hex_triplet)
  (e.g. `"0x000"`, `"#FFFFFF"`, `"7fffd4"`)
- RGB/RGBA tuples (e.g. `(255, 255, 255)`, `(255, 255, 255, 0.5)`
- [RGB/RGBA strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#RGB_colors)
  (e.g. `"rgb(255, 255, 255)"` or `"rgba(255, 255, 255, 0.5)"`)
- [HSL strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#HSL_colors)
  (e.g. `"hsl(270, 60%, 70%)"` or `"hsl(270, 60%, 70%, .5)"`)

```py
{!./examples/ex_color_type.py!}
```

(This script is complete, it should run "as is")

`Color` has the following methods:

* **`original`** the original string or tuple passed to `Color`
* **`as_named`** returns a named CSS3 color, fails if the alpha channel is set or no such color exists unless
  `fallback=True` is supplied when it falls back to `as_hex`
* **`as_hex`** string in the format `#ffffff` or `#fff`, can also be a 4 or 8 hex values if the alpha channel is set,
  e.g. `#7f33cc26`
* **`as_rgb`** string in the format `rgb(<red>, <green>, <blue>)` or `rgba(<red>, <green>, <blue>, <alpha>)`
  if the alpha channel is set
* **`as_rgb_tuple`** returns a 3- or 4-tuple in RGB(a) format, the `alpha` keyword argument can be used to define whether
  the alpha channel should be included,
  options: `True` - always include, `False` - never include, `None` (the default) - include if set
* **`as_hsl`** string in the format `hsl(<hue deg>, <saturation %>, <lightness %>)`
  or `hsl(<hue deg>, <saturation %>, <lightness %>, <alpha>)` if the alpha channel is set
* **`as_hsl_tuple`** returns a 3- or 4-tuple in HSL(a) format, the `alpha` keyword argument can be used to define whether
  the alpha channel should be included,
  options: `True` - always include, `False` - never include, `None` (the default)  - include if set

The `__str__` method for `Color` returns `self.as_named(fallback=True)`.

!!! note
    the `as_hsl*` refer to hue, saturation, lightness "HSL" as used in html and most of the world, **not**
    "HLS" as used in python's `colorsys`.

### Secret Types

You can use the `SecretStr` and the `SecretBytes` data types for storing sensitive information
that you do not want to be visible in logging or tracebacks.
The SecretStr and SecretBytes will be formatted as either `'**********'` or `''` on conversion to json.

```py
{!./examples/ex_secret_types.py!}
```

(This script is complete, it should run "as is")

### Strict Types

You can use the `StrictStr`, `StrictInt`, `StrictFloat`, and `StrictBool` types
to prevent coercion from compatible types.
These types will only pass validation when the validated value is of the respective type or is a subtype of that type.
This behavior is also exposed via the `strict` field of the `ConstrainedStr`, `ConstrainedFloat` and
`ConstrainedInt` classes and can be combined with a multitude of complex validation rules.

The following caveats apply:

- `StrictInt` (and the `strict` option of `ConstrainedInt`) will not accept `bool` types,
    even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `ConstrainedFloat`) will not accept `int`.

```py
{!./examples/strict_types.py!}
```

(This script is complete, it should run "as is")

### Json Type

You can use `Json` data type - *Pydantic* will first parse raw JSON string and then will validate parsed object
against defined Json structure if it's provided.

```py
{!./examples/ex_json_type.py!}
```

(This script is complete, it should run "as is")

### Literal Type

Pydantic supports the use of `typing_extensions.Literal` as a lightweight way to specify that a field
may accept only specific literal values:

```py
{!./examples/literal1.py!}
```

(This script is complete, it should run "as is")

One benefit of this field type is that it can be used to check for equality with one or more specific values
without needing to declare custom validators:

```py
{!./examples/literal2.py!}
```

(This script is complete, it should run "as is")

With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity:

```py
{!./examples/literal3.py!}
```

(This script is complete, it should run "as is")

### Payment Card Numbers

The [`PaymentCardNumber`` type validates `payment cards](https://en.wikipedia.org/wiki/Payment_card)
(such as a debit or credit card).

```py
{!./examples/payment_card_number.py!}
```

(This script is complete, it should be run "as is")

`PaymentCardBrand` can be one of the following based on the BIN:

* `PaymentCardBrand.amex`
* `PaymentCardBrand.mastercard`
* `PaymentCardBrand.visa`
* `PaymentCardBrand.other`

The actual validation verifies the card number is:

* a `str` of only digits
* [luhn](https://en.wikipedia.org/wiki/Luhn_algorithm) valid
* the correct length based on the BIN, if Amex, Mastercard or Visa, and between
  12 and 19 digits for all other brands

### Type Type

Pydantic supports the use of `Type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

```py
{!./examples/type_type.py!}
```

You may also use `Type` to specify that any class is allowed.

```py
{!./examples/bare_type_type.py!}
```

### Custom Data Types

You can also define your own data types. The class method `__get_validators__` will be called
to get validators to parse and validate the input data.

!!! note
    The name of `__get_validators__` was changed from `get_validators` in `v0.17`,
    the old name is currently still supported but deprecated and will be removed in future.

```py
{!./examples/custom_data_types.py!}
```

(This script is complete, it should run "as is")

### Custom Root Types

Pydantic models which do not represent a `dict` ("object" in JSON parlance) can have a custom
root type defined via the `__root__` field. The root type can of any type: list, float, int etc.

The root type can be defined via the type hint on the `__root__` field.
The root value can be passed to model `__init__` via the `__root__` keyword argument or as
the first and only argument to `parse_obj`.

```py
{!examples/custom_root_field.py!}
```

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

### Model Config

Behaviour of pydantic can be controlled via the `Config` class on a model.

Options:

* **`title`** title for the generated JSON Schema
* **`anystr_strip_whitespace`** strip or not trailing and leading whitespace for str & byte types (default: `False`)
* **`min_anystr_length`** min length for str & byte types (default: `0`)
* **`max_anystr_length`** max length for str & byte types (default: `2 ** 16`)
* **`validate_all`** whether or not to validate field defaults (default: `False`)
* **`extra`** whether to ignore, allow or forbid extra attributes in model. Can use either string values of `ignore`,
  `allow` or `forbid`, or use `Extra` enum (default is `Extra.ignore`)
* **`allow_mutation`** whether or not models are faux-immutable, e.g. __setattr__ fails (default: `True`)
* **`use_enum_values`** whether to populate models with the `value` property of enums,
    rather than the raw enum - useful if you want to serialise `model.dict()` later (default: `False`)
* **`fields`** schema information on each field, this is equivilant to
    using [the schema](usage.md#schema) class (default: `None`)
* **`validate_assignment`** whether to perform validation on assignment to attributes or not (default: `False`)
* **`allow_population_by_alias`** whether or not an aliased field may be populated by its name as given by the model
    attribute, rather than strictly the alias; please be sure to read the warning below before enabling this (default:
    `False`)
* **`error_msg_templates`** let's you to override default error message templates.
    Pass in a dictionary with keys matching the error messages you want to override (default: `{}`)
* **`arbitrary_types_allowed`** whether to allow arbitrary user types for fields (they are validated simply by checking if the
    value is instance of that type). If `False` - `RuntimeError` will be raised on model declaration (default: `False`)
* **`orm_mode`** allows usage of [ORM mode](usage.md#orm_mode)
* **`getter_dict`** custom class (should inherit from `GetterDict`) to use when decomposing ORM classes for validation,
  use with `orm_mode`
* **`alias_generator`** callable that takes field name and returns alias for it
* **`keep_untouched`** tuple of types (e. g. descriptors) that won't change during model creation and won't be
  included in the model schemas
* **`schema_extra`** takes a `dict` to extend/update the generated JSON Schema
* **`json_loads`** custom function for decoding JSON, see [custom JSON (de)serialisation](usage.md#custom-json-deserialisation)
* **`json_dumps`** custom function for encoding JSON, see [custom JSON (de)serialisation](usage.md#custom-json-deserialisation)
* **`json_encoders`** customise the way types are encoded to JSON, see [JSON Serialisation](usage.md#modeljson)

!!! warning
    Think twice before enabling `allow_population_by_alias`! Enabling it could cause previously correct code to become
    subtly incorrect. As an example, say you have a field named `card_number` with the alias `cardNumber`. With
    population by alias disabled (the default), trying to parse an object with only the key `card_number` will fail.
    However, if you enable population by alias, the `card_number` field can now be populated from `cardNumber`
    **or** `card_number`, and the previously-invalid example object would now be valid. This may be desired for some
    use cases, but in others (like the one given here, perhaps!), relaxing strictness with respect to aliases could
    introduce bugs.

```py
{!./examples/config.py!}
```

(This script is complete, it should run "as is")

Version for models based on `@dataclass` decorator:

```py
{!./examples/ex_dataclasses_config.py!}
```

(This script is complete, it should run "as is")

#### Alias Generator

If data source field names do not match your code style (e. g. CamelCase fields),
you can automatically generate aliases using `alias_generator`:

```py
{!./examples/alias_generator_config.py!}
```

(This script is complete, it should run "as is")

### Settings

One of pydantic's most useful applications is to define default settings, allow them to be overridden by
environment variables or keyword arguments (e.g. in unit tests).

```py
{!./examples/settings.py!}
```

(This script is complete, it should run "as is")

The following rules apply when finding and interpreting environment variables:

* When no custom environment variable name(s) are given, the environment variable name is built using the field
  name and prefix, eg to override `special_function` use `export my_prefix_special_function='foo.bar'`, the default
  prefix is an empty string. aliases are ignored for building the environment variable name.
* Custom environment variable names can be set using with `Config.fields.[field name].env` or `Field(..., env=...)`,
  in the above example `auth_key` and `api_key`'s environment variable setups are the equivalent.
* In these cases `env` can either be a string or a list of strings. When a list of strings order is important:
  in the case of `redis_dsn` `service_redis_dsn` would take precedence over `redis_url`.

!!! warning
    Since V1 *pydantic* does not consider field aliases when finding environment variables to populate settings
    models, use `env` instead as described above.

    To aid the transition from aliases to `env`, a warning will be raised when aliases are used on settings models
    without a custom env var name. If you really mean to use aliases, either ignore the warning or set `env` to
    suppress it.

By default `BaseSettings` considers field values in the following priority (where 3. has the highest priority
and overrides the other two):

1. The default values set in your `Settings` class.
2. Environment variables, e.g. `my_prefix_special_function` as described above.
3. Arguments passed to the `Settings` class on initialisation.

Complex types like `list`, `set`, `dict` and sub-models can be set by using JSON environment variables.

Case-sensitivity can be turned on through `Config`:

```py
{!./examples/settings_case_sensitive.py!}
```

When `case_sensitive` is `True`, the environment variable must be in all-caps,
so in this example `redis_host` could only be modified via `export REDIS_HOST`.

!!! note
    On Windows, python's `os` module always treats environment variables as case-insensitive, so the
    `case_sensitive` config setting will have no effect -- settings will always be updated ignoring case.

### Dynamic model creation

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

### Usage with mypy

Pydantic works with [mypy](http://mypy-lang.org/) provided you use the "annotation only" version of
required variables:

```py
{!./examples/mypy.py!}
```

(This script is complete, it should run "as is")

You can also run it through mypy with:

    mypy --ignore-missing-imports --follow-imports=skip --strict-optional pydantic_mypy_test.py

#### Strict Optional

For your code to pass with `--strict-optional` you need to to use `Optional[]` or an alias of `Optional[]`
for all fields with `None` default, this is standard with mypy.

Pydantic provides a few useful optional or union types:

* `NoneStr` aka. `Optional[str]`
* `NoneBytes` aka. `Optional[bytes]`
* `StrBytes` aka. `Union[str, bytes]`
* `NoneStrBytes` aka. `Optional[StrBytes]`

If these aren't sufficient you can of course define your own.

#### Required Fields and mypy

The ellipsis notation `...` will not work with mypy, you need to use annotation only fields as in the example above.

To get round this you can use the `Required` (via `from pydantic import Required`) field as an alias for
ellipses or annotation only.

### Faux Immutability

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

### Exporting Models

As well as accessing model attributes directly via their names (eg. `model.foobar`), models can be converted
and exported in a number of ways:

#### `model.dict(...)`

The primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

Arguments:

* `include`: fields to include in the returned dictionary, see [below](usage.md#include_exclude)
* `exclude`: fields to exclude from the returned dictionary, see [below](usage.md#include_exclude)
* `by_alias`: whether field aliases should be used as keys in the returned dictionary, default `False`
* `skip_defaults`: whether fields which were not set when creating the model and have their default values should
  be excluded from the returned dictionary, default `False`

Example:

```py
{!./examples/export_dict.py!}
```

(This script is complete, it should run "as is")

#### `dict(model)` and iteration

*pydantic* models can also be converted to dictionaries using `dict(model)`, you can also
iterate over a model's field using `for field_name, value in model:`. Here the raw field values are returned, eg.
sub-models will not be converted to dictionaries.

Example:

```py
{!./examples/export_iterate.py!}
```

(This script is complete, it should run "as is")

#### `model.copy(...)`

`copy()` allows models to be duplicated, this is particularly useful for immutable models.

Arguments:

* `include`: fields to include in the returned dictionary, see [below](usage.md#include_exclude)
* `exclude`: fields to exclude from the returned dictionary, see [below](usage.md#include_exclude)
* `update`: dictionaries of values to change when creating the new model
* `deep`: whether to make a deep copy of the new model, default `False`

Example:

```py
{!./examples/export_copy.py!}
```

(This script is complete, it should run "as is")

#### `model.json(...)`

The `.json()` method will serialise a model to JSON. Typically, `.json()` in turn calls `.dict()` and
serialises its result. (For models with a [custom root type](usage.md#custom_root), after calling `.dict()`,
only the value for the `__root__` key is serialised.)

Serialisation can be customised on a model using the `json_encoders` config property, the keys should be types and
the values should be functions which serialise that type, see the example below.

Arguments:

* `include`: fields to include in the returned dictionary, see [below](usage.md#include_exclude)
* `exclude`: fields to exclude from the returned dictionary, see [below](usage.md#include_exclude)
* `by_alias`: whether field aliases should be used as keys in the returned dictionary, default `False`
* `skip_defaults`: whether fields which were not set when creating the model and have their default values should
  be excluded from the returned dictionary, default `False`
* `encoder`: a custom encoder function passed to the `default` argument of `json.dumps()`, defaults to a custom
  encoder designed to take care of all common types
* `**dumps_kwargs`: any other keyword argument are passed to `json.dumps()`, eg. `indent`.

Example:

```py
{!./examples/export_json.py!}
```

(This script is complete, it should run "as is")

By default timedelta's are encoded as a simple float of total seconds. The `timedelta_isoformat` is provided
as an optional alternative which implements ISO 8601 time diff encoding.

See [below](usage.md#json_encode_decode) for details on how to use other libraries for more performant JSON encoding
and decoding

#### `pickle.dumps(model)`

Using the same plumbing as `copy()` *pydantic* models support efficient pickling and unpicking.

```py
{!./examples/export_pickle.py!}
```

(This script is complete, it should run "as is")

### Advanced include and exclude

The `dict`, `json` and `copy` methods support `include` and `exclude` arguments which can either be
sets or dictionaries, allowing nested selection of which fields to export:

```py
{!./examples/advanced_exclude1.py!}
```

The `...` value indicates that we want to exclude or include entire key, just as if we included it in a set.

Of course same can be done on any depth level:

```py
{!./examples/advanced_exclude2.py!}
```

Same goes for `json` and `copy` methods.

### Custom JSON (de)serialisation

To improve the performance of encoding and decoding JSON, alternative JSON implementations can be used via the
[`json_loads`` and `json_dumps` properties of `Config`, e.g. `ujson](https://pypi.python.org/pypi/ujson).

```py
{!./examples/json_ujson.py!}
```

(This script is complete, it should run "as is")

`ujson` generally cannot be used to dump JSON since it doesn't support encoding of objects like datetimes and does
not accept a `default` fallback function argument. To do this you may use another library like
[orjson](https://github.com/ijl/orjson).

```py
{!./examples/json_orjson.py!}
```

(This script is complete, it should run "as is")

Note that `orjson` takes care of `datetime` encoding natively, making it faster than `json.dumps` but
meaning you cannot always customise encoding using `Config.json_encoders`.

### Abstract Base Classes

Pydantic models can be used alongside Python's
[Abstract Base Classes](https://docs.python.org/3/library/abc.html) (ABCs).

```py
{!./examples/ex_abc.py!}
```

(This script is complete, it should run "as is")

### Postponed Annotations

!!! note
    Both postponed annotations via the future import and `ForwardRef` require python 3.7+.

    Support for those features starts from *pydantic* v0.18.

Postponed annotations (as described in [PEP563](https://www.python.org/dev/peps/pep-0563/))
"just work".

```py
{!./examples/postponed_annotations.py!}
```

(This script is complete, it should run "as is")

Internally *pydantic*  will call a method similar to `typing.get_type_hints` to resolve annotations.

In cases where the referenced type is not yet defined, `ForwardRef` can be used (although referencing the
type directly or by its string is a simpler solution in the case of
[self-referencing models](usage.md#self_ref_models)).

You may need to call `Model.update_forward_refs()` after creating the model,
this is because in the example below `Foo` doesn't exist before it has been created (obviously) so `ForwardRef`
can't initially be resolved. You have to wait until after `Foo` is created, then call `update_forward_refs`
to properly set types before the model can be used.

```py
{!./examples/forward_ref.py!}
```

(This script is complete, it should run "as is")

!!! warning
    To resolve strings (type names) into annotations (types) *pydantic* needs a dict to lookup,
    for this is uses `module.__dict__` just as `get_type_hints` does. That means *pydantic* does not play well
    with types not defined in the global scope of a module.

For example, this works fine:

```py
{!./examples/postponed_works.py!}
```

While this will break:

```py
{!./examples/postponed_broken.py!}
```

Resolving this is beyond the call for *pydantic*: either remove the future import or declare the types globally.

### Usage of `Union` in Annotations and Type Order

The `Union` type allows a model attribute to accept different types, e.g.:

**(This script is complete, it should run but may be is wrong, see below)**

```py
{!./examples/union_type_incorrect.py!}
```

However, as can be seen above, *pydantic* will attempt to 'match' any of the types defined under `Union` and will use
the first one that matches. In the above example the `id` of `user_03` was defined as a `uuid.UUID` class (which
is defined under the attribute's `Union` annotation) but as the `uuid.UUID` can be marshalled into an `int` it
chose to match against the `int` type and disregarded the other types.

As such, it is recommended that when defining `Union` annotations that the most specific type is defined first and
followed by less specific types. In the above example, the `UUID` class should precede the `int` and `str`
classes to preclude the unexpected representation as such:

```py
{!./examples/union_type_correct.py!}
```
