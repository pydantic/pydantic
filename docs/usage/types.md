Where possible *pydantic* uses [standard library types](#standard-library-types) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so *pydantic* implements [many commonly used types](#pydantic-types).

If no existing type suits your purpose you can also implement your [own pydantic-compatible types](#custom-data-types)
with custom properties and validation.

## Standard Library Types

*pydantic* supports many common types from the Python standard library. If you need stricter processing see
[Strict Types](#strict-types); if you need to constrain the values allowed (e.g. to require a positive int) see
[Constrained Types](#constrained-types).

`None`, `type(None)` or `Literal[None]` (equivalent according to [PEP 484](https://www.python.org/dev/peps/pep-0484/#using-none))
: allows only `None` value

`bool`
: see [Booleans](#booleans) below for details on how bools are validated and what values are permitted

`int`
: *pydantic* uses `int(v)` to coerce types to an `int`;
  see [this](models.md#data-conversion) warning on loss of information during data conversion

`float`
: similarly, `float(v)` is used to coerce values to floats

`str`
: strings are accepted as-is, `int` `float` and `Decimal` are coerced using `str(v)`, `bytes` and `bytearray` are
  converted using `v.decode()`, enums inheriting from `str` are converted using `v.value`,
  and all other types cause an error

`bytes`
: `bytes` are accepted as-is, `bytearray` is converted using `bytes(v)`, `str` are converted using `v.encode()`,
  and `int`, `float`, and `Decimal` are coerced using `str(v).encode()`

`list`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a list;
  see `typing.List` below for sub-type constraints

`tuple`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a tuple;
  see `typing.Tuple` below for sub-type constraints

`dict`
: `dict(v)` is used to attempt to convert a dictionary;
  see `typing.Dict` below for sub-type constraints

`set`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a set;
  see `typing.Set` below for sub-type constraints

`frozenset`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a frozen set;
  see `typing.FrozenSet` below for sub-type constraints

`deque`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a deque;
  see `typing.Deque` below for sub-type constraints

`datetime.date`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.time`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.datetime`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.timedelta`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`typing.Any`
: allows any value including `None`, thus an `Any` field is optional

`typing.Annotated`
: allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The
  `Annotated` hint may contain a single call to the [`Field` function](schema.md#typingannotated-fields), but otherwise
  the additional metadata is ignored and the root type is used.

`typing.TypeVar`
: constrains the values allowed based on `constraints` or `bound`, see [TypeVar](#typevar)

`typing.Union`
: see [Unions](#unions) below for more detail on parsing and validation

`typing.Optional`
: `Optional[x]` is simply short hand for `Union[x, None]`;
  see [Unions](#unions) below for more detail on parsing and validation and [Required Fields](models.md#required-fields) for details about required fields that can receive `None` as a value.

`typing.List`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Tuple`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`subclass of typing.NamedTuple`
: Same as `tuple` but instantiates with the given namedtuple and validates fields since they are annotated.
  See [Annotated Types](#annotated-types) below for more detail on parsing and validation

`subclass of collections.namedtuple`
: Same as `subclass of typing.NamedTuple` but all fields will have type `Any` since they are not annotated

`typing.Dict`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`subclass of typing.TypedDict`
: Same as `dict` but _pydantic_ will validate the dictionary since keys are annotated.
  See [Annotated Types](#annotated-types) below for more detail on parsing and validation

`typing.Set`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.FrozenSet`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Deque`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Sequence`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Iterable`
: this is reserved for iterables that shouldn't be consumed. See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation

`typing.Type`
: see [Type](#type) below for more detail on parsing and validation

`typing.Callable`
: see [Callable](#callable) below for more detail on parsing and validation

`typing.Pattern`
: will cause the input value to be passed to `re.compile(v)` to create a regex pattern

`ipaddress.IPv4Address`
: simply uses the type itself for validation by passing the value to `IPv4Address(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv4Interface`
: simply uses the type itself for validation by passing the value to `IPv4Address(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv4Network`
: simply uses the type itself for validation by passing the value to `IPv4Network(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv6Address`
: simply uses the type itself for validation by passing the value to `IPv6Address(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv6Interface`
: simply uses the type itself for validation by passing the value to `IPv6Interface(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv6Network`
: simply uses the type itself for validation by passing the value to `IPv6Network(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`enum.Enum`
: checks that the value is a valid Enum instance

`subclass of enum.Enum`
: checks that the value is a valid member of the enum;
  see [Enums and Choices](#enums-and-choices) for more details

`enum.IntEnum`
: checks that the value is a valid IntEnum instance

`subclass of enum.IntEnum`
: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](#enums-and-choices) for more details

`decimal.Decimal`
: *pydantic* attempts to convert the value to a string, then passes the string to `Decimal(v)`

`pathlib.Path`
: simply uses the type itself for validation by passing the value to `Path(v)`;
  see [Pydantic Types](#pydantic-types) for other more strict path types

`uuid.UUID`
: strings and bytes (converted to strings) are passed to `UUID(v)`, with a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`;
  see [Pydantic Types](#pydantic-types) for other stricter UUID types

`ByteSize`
: converts a bytes string with units to bytes

### Typing Iterables

*pydantic* uses standard library `typing` types as defined in PEP 484 to define complex objects.

```py
{!.tmp_examples/types_iterables.py!}
```
_(This script is complete, it should run "as is")_

### Infinite Generators

If you have a generator you can use `Sequence` as described above. In that case, the
generator will be consumed and stored on the model as a list and its values will be
validated with the sub-type of `Sequence` (e.g. `int` in `Sequence[int]`).

But if you have a generator that you don't want to be consumed, e.g. an infinite
generator or a remote data loader, you can define its type with `Iterable`:

```py
{!.tmp_examples/types_infinite_generator.py!}
```
_(This script is complete, it should run "as is")_

!!! warning
    `Iterable` fields only perform a simple check that the argument is iterable and
    won't be consumed.

    No validation of their values is performed as it cannot be done without consuming
    the iterable.

!!! tip
    If you want to validate the values of an infinite generator you can create a
    separate model and use it while consuming the generator, reporting the validation
    errors as appropriate.

    pydantic can't validate the values automatically for you because it would require
    consuming the infinite generator.

#### Validating the first value

You can create a [validator](validators.md) to validate the first value in an infinite generator and still not consume it entirely.

```py
{!.tmp_examples/types_infinite_generator_validate_first.py!}
```
_(This script is complete, it should run "as is")_

### Unions

The `Union` type allows a model attribute to accept different types, e.g.:

!!! info
    You may get unexpected coercion with `Union`; see below.<br />
    Know that you can also make the check slower but stricter by using [Smart Union](model_config.md#smart-union)

```py
{!.tmp_examples/types_union_incorrect.py!}
```
_(This script is complete, it should run "as is")_

However, as can be seen above, *pydantic* will attempt to 'match' any of the types defined under `Union` and will use
the first one that matches. In the above example the `id` of `user_03` was defined as a `uuid.UUID` class (which
is defined under the attribute's `Union` annotation) but as the `uuid.UUID` can be marshalled into an `int` it
chose to match against the `int` type and disregarded the other types.

!!! warning
    `typing.Union` also ignores order when [defined](https://docs.python.org/3/library/typing.html#typing.Union),
    so `Union[int, float] == Union[float, int]` which can lead to unexpected behaviour
    when combined with matching based on the `Union` type order inside other type definitions, such as `List` and `Dict`
    types (because Python treats these definitions as singletons).
    For example, `Dict[str, Union[int, float]] == Dict[str, Union[float, int]]` with the order based on the first time it was defined.
    Please note that this can also be [affected by third party libraries](https://github.com/pydantic/pydantic/issues/2835)
    and their internal type definitions and the import orders.

As such, it is recommended that, when defining `Union` annotations, the most specific type is included first and
followed by less specific types.

In the above example, the `UUID` class should precede the `int` and `str` classes to preclude the unexpected representation as such:

```py
{!.tmp_examples/types_union_correct.py!}
```
_(This script is complete, it should run "as is")_

!!! tip
    The type `Optional[x]` is a shorthand for `Union[x, None]`.

    `Optional[x]` can also be used to specify a required field that can take `None` as a value.

    See more details in [Required Fields](models.md#required-fields).

#### Discriminated Unions (a.k.a. Tagged Unions)

When `Union` is used with multiple submodels, you sometimes know exactly which submodel needs to
be checked and validated and want to enforce this.
To do that you can set the same field - let's call it `my_discriminator` - in each of the submodels
with a discriminated value, which is one (or many) `Literal` value(s).
For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

Setting a discriminated union has many benefits:

- validation is faster since it is only attempted against one model
- only one explicit error is raised in case of failure
- the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#discriminatorObject)

```py
{!.tmp_examples/types_union_discriminated.py!}
```
_(This script is complete, it should run "as is")_

!!! note
    Using the [Annotated Fields syntax](../schema/#typingannotated-fields) can be handy to regroup
    the `Union` and `discriminator` information. See below for an example!

!!! warning
    Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

    Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to
    distinguish fields of `Union[T]` from `T`.

#### Nested Discriminated Unions

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
In this case you can always create "intermediate" models with `__root__` and add your discriminator.

```py
{!.tmp_examples/types_union_discriminated_nested.py!}
```
_(This script is complete, it should run "as is")_

### Enums and Choices

*pydantic* uses Python's standard `enum` classes to define choices.

```py
{!.tmp_examples/types_choices.py!}
```
_(This script is complete, it should run "as is")_


### Datetime Types

*Pydantic* supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
types:

* `datetime` fields can be:

  * `datetime`, existing `datetime` object
  * `int` or `float`, assumed as Unix time, i.e. seconds (if >= `-2e10` or <= `2e10`) or milliseconds (if < `-2e10`or > `2e10`) since 1 January 1970
  * `str`, following formats work:

    * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]]]`
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

    * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]]]`

* `timedelta` fields can be:

  * `timedelta`, existing `timedelta` object
  * `int` or `float`, assumed as seconds
  * `str`, following formats work:

    * `[-][DD ][HH:MM]SS[.ffffff]`
    * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)

```py
{!.tmp_examples/types_dt.py!}
```

### Booleans

!!! warning
    The logic for parsing `bool` fields has changed as of version **v1.0**.

    Prior to **v1.0**, `bool` parsing never failed, leading to some unexpected results.
    The new logic is described below.

A standard `bool` field will raise a `ValidationError` if the value is not one of the following:

* A valid boolean (i.e. `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of
  `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid (per the previous rule) when decoded to `str`

!!! note
    If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can
    use [`StrictBool`](#strict-types).

Here is a script demonstrating some of these behaviors:

```py
{!.tmp_examples/types_boolean.py!}
```
_(This script is complete, it should run "as is")_

### Callable

Fields can also be of type `Callable`:

```py
{!.tmp_examples/types_callable.py!}
```
_(This script is complete, it should run "as is")_

!!! warning
    Callable fields only perform a simple check that the argument is
    callable; no validation of arguments, their types, or the return
    type is performed.

### Type

*pydantic* supports the use of `Type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

```py
{!.tmp_examples/types_type.py!}
```
_(This script is complete, it should run "as is")_

You may also use `Type` to specify that any class is allowed.

```py
{!.tmp_examples/types_bare_type.py!}
```
_(This script is complete, it should run "as is")_

### TypeVar

`TypeVar` is supported either unconstrained, constrained or with a bound.

```py
{!.tmp_examples/types_typevar.py!}
```
_(This script is complete, it should run "as is")_

## Literal Type

!!! note
    This is a new feature of the Python standard library as of Python 3.8;
    prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.

*pydantic* supports the use of `typing.Literal` (or `typing_extensions.Literal` prior to Python 3.8)
as a lightweight way to specify that a field may accept only specific literal values:

```py
{!.tmp_examples/types_literal1.py!}
```
_(This script is complete, it should run "as is")_

One benefit of this field type is that it can be used to check for equality with one or more specific values
without needing to declare custom validators:

```py
{!.tmp_examples/types_literal2.py!}
```
_(This script is complete, it should run "as is")_

With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity:

```py
{!.tmp_examples/types_literal3.py!}
```
_(This script is complete, it should run "as is")_

## Annotated Types

### NamedTuple

```py
{!.tmp_examples/annotated_types_named_tuple.py!}
```
_(This script is complete, it should run "as is")_

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.
    But required and optional fields are properly differentiated only since Python 3.9.
    We therefore recommend using [typing-extensions](https://pypi.org/project/typing-extensions/) with Python 3.8 as well.


```py
{!.tmp_examples/annotated_types_typed_dict.py!}
```
_(This script is complete, it should run "as is")_

## Pydantic Types

*pydantic* also provides a variety of other useful types:

`FilePath`
: like `Path`, but the path must exist and be a file

`DirectoryPath`
: like `Path`, but the path must exist and be a directory

`PastDate`
: like `date`, but the date should be in the past

`FutureDate`
: like `date`, but the date should be in the future

`EmailStr`
: requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed;
  the input string must be a valid email address, and the output is a simple string



`NameEmail`
: requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed;
  the input string must be either a valid email address or in the format `Fred Bloggs <fred.bloggs@example.com>`,
  and the output is a `NameEmail` object which has two properties: `name` and `email`.
  For `Fred Bloggs <fred.bloggs@example.com>` the name would be `"Fred Bloggs"`;
  for `fred.bloggs@example.com` it would be `"fred.bloggs"`.


`PyObject`
: expects a string and loads the Python object importable at that dotted path;
  e.g. if `'math.cos'` was provided, the resulting field value would be the function `cos`

`Color`
: for parsing HTML and CSS colors; see [Color Type](#color-type)

`Json`
: a special type wrapper which loads JSON before parsing; see [JSON Type](#json-type)

`PaymentCardNumber`
: for parsing and validating payment cards; see [payment cards](#payment-card-numbers)

`AnyUrl`
: any URL; see [URLs](#urls)

`AnyHttpUrl`
: an HTTP URL; see [URLs](#urls)

`HttpUrl`
: a stricter HTTP URL; see [URLs](#urls)

`FileUrl`
: a file path URL; see [URLs](#urls)

`PostgresDsn`
: a postgres DSN style URL; see [URLs](#urls)

`CockroachDsn`
: a cockroachdb DSN style URL; see [URLs](#urls)

`RabbitMqDsn`
: an `AMQP` DSN style URL as used by RabbitMQ, StormMQ, ActiveMQ etc.; see [URLs](#urls)

`RedisDsn`
: a redis DSN style URL; see [URLs](#urls)

`MongoDsn`
: a MongoDB DSN style URL; see [URLs](#urls)

`KafkaDsn`
: a kafka DSN style URL; see [URLs](#urls)

`stricturl`
: a type method for arbitrary URL constraints; see [URLs](#urls)

`UUID1`
: requires a valid UUID of type 1; see `UUID` [above](#standard-library-types)

`UUID3`
: requires a valid UUID of type 3; see `UUID` [above](#standard-library-types)

`UUID4`
: requires a valid UUID of type 4; see `UUID` [above](#standard-library-types)

`UUID5`
: requires a valid UUID of type 5; see `UUID` [above](#standard-library-types)

`SecretBytes`
: bytes where the value is kept partially secret; see [Secrets](#secret-types)

`SecretStr`
: string where the value is kept partially secret; see [Secrets](#secret-types)

`IPvAnyAddress`
: allows either an `IPv4Address` or an `IPv6Address`

`IPvAnyInterface`
: allows either an `IPv4Interface` or an `IPv6Interface`

`IPvAnyNetwork`
: allows either an `IPv4Network` or an `IPv6Network`

`NegativeFloat`
: allows a float which is negative; uses standard `float` parsing then checks the value is less than 0;
  see [Constrained Types](#constrained-types)

`NegativeInt`
: allows an int which is negative; uses standard `int` parsing then checks the value is less than 0;
  see [Constrained Types](#constrained-types)

`PositiveFloat`
: allows a float which is positive; uses standard `float` parsing then checks the value is greater than 0;
  see [Constrained Types](#constrained-types)

`PositiveInt`
: allows an int which is positive; uses standard `int` parsing then checks the value is greater than 0;
  see [Constrained Types](#constrained-types)

`conbytes`
: type method for constraining bytes;
  see [Constrained Types](#constrained-types)

`condecimal`
: type method for constraining Decimals;
  see [Constrained Types](#constrained-types)

`confloat`
: type method for constraining floats;
  see [Constrained Types](#constrained-types)

`conint`
: type method for constraining ints;
  see [Constrained Types](#constrained-types)

`conlist`
: type method for constraining lists;
  see [Constrained Types](#constrained-types)

`conset`
: type method for constraining sets;
  see [Constrained Types](#constrained-types)

`confrozenset`
: type method for constraining frozen sets;
  see [Constrained Types](#constrained-types)

`constr`
: type method for constraining strs;
  see [Constrained Types](#constrained-types)

### URLs

For URI/URL validation the following types are available:

- `AnyUrl`: any scheme allowed, TLD not required, host required
- `AnyHttpUrl`: scheme `http` or `https`, TLD not required, host required
- `HttpUrl`: scheme `http` or `https`, TLD required, host required, max length 2083
- `FileUrl`: scheme `file`, host not required
- `PostgresDsn`: user info required, TLD not required, host required,
  as of V.10 `PostgresDsn` supports multiple hosts. The following schemes are supported:
  - `postgres`
  - `postgresql`
  - `postgresql+asyncpg`
  - `postgresql+pg8000`
  - `postgresql+psycopg2`
  - `postgresql+psycopg2cffi`
  - `postgresql+py-postgresql`
  - `postgresql+pygresql`
- `CockroachDsn`: scheme `cockroachdb`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `cockroachdb+asyncpg`
  - `cockroachdb+psycopg2`
- `AmqpDsn`: schema `amqp` or `amqps`, user info not required, TLD not required, host not required
- `RedisDsn`: scheme `redis` or `rediss`, user info not required, tld not required, host not required (CHANGED: user info
- `MongoDsn` : scheme `mongodb`, user info not required, database name not required, port
  not required from **v1.6** onwards), user info may be passed without user part (e.g., `rediss://:pass@localhost`)
- `stricturl`: method with the following keyword arguments:
    - `strip_whitespace: bool = True`
    - `min_length: int = 1`
    - `max_length: int = 2 ** 16`
    - `tld_required: bool = True`
    - `host_required: bool = True`
    - `allowed_schemes: Optional[Set[str]] = None`

The above types (which all inherit from `AnyUrl`) will attempt to give descriptive errors when invalid URLs are
provided:

```py
{!.tmp_examples/types_urls.py!}
```
_(This script is complete, it should run "as is")_

If you require a custom URI/URL type, it can be created in a similar way to the types defined above.

#### URL Properties

Assuming an input URL of `http://samuel:pass@example.com:8000/the/path/?query=here#fragment=is;this=bit`,
the above types export the following properties:

- `scheme`: always set - the url scheme (`http` above)
- `host`: always set - the url host (`example.com` above)
- `host_type`: always set - describes the type of host, either:

  - `domain`: e.g. `example.com`,
  - `int_domain`: international domain, see [below](#international-domains), e.g. `exampl£e.org`,
  - `ipv4`: an IP V4 address, e.g. `127.0.0.1`, or
  - `ipv6`: an IP V6 address, e.g. `2001:db8:ff00:42`

- `user`: optional - the username if included (`samuel` above)
- `password`: optional - the password if included (`pass` above)
- `tld`: optional - the top level domain (`com` above),
  **Note: this will be wrong for any two-level domain, e.g. "co.uk".** You'll need to implement your own list of TLDs
  if you require full TLD validation
- `port`: optional - the port (`8000` above)
- `path`: optional - the path (`/the/path/` above)
- `query`: optional - the URL query (aka GET arguments or "search string") (`query=here` above)
- `fragment`: optional - the fragment (`fragment=is;this=bit` above)

If further validation is required, these properties can be used by validators to enforce specific behaviour:

```py
{!.tmp_examples/types_url_properties.py!}
```
_(This script is complete, it should run "as is")_

#### International Domains

"International domains" (e.g. a URL where the host or TLD includes non-ascii characters) will be encoded via
[punycode](https://en.wikipedia.org/wiki/Punycode) (see
[this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```py
{!.tmp_examples/types_url_punycode.py!}
```
_(This script is complete, it should run "as is")_


!!! warning
    #### Underscores in Hostnames

    In *pydantic* underscores are allowed in all parts of a domain except the tld.
    Technically this might be wrong - in theory the hostname cannot have underscores, but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk`: the hostname is `exam_ple`, which should not be allowed since it contains an underscore
    - `foo_bar.example.com` the hostname is `example`, which should be allowed since the underscore is in the subdomain

    Without having an exhaustive list of TLDs, it would be impossible to differentiate between these two. Therefore
    underscores are allowed, but you can always do further validation in a validator if desired.

    Also, Chrome, Firefox, and Safari all currently accept `http://exam_ple.com` as a URL, so we're in good
    (or at least big) company.

### Color Type

You can use the `Color` data type for storing colors as per
[CSS3 specification](http://www.w3.org/TR/css3-color/#svg-color). Colors can be defined via:

- [name](http://www.w3.org/TR/SVG11/types.html#ColorKeywords) (e.g. `"Black"`, `"azure"`)
- [hexadecimal value](https://en.wikipedia.org/wiki/Web_colors#Hex_triplet)
  (e.g. `"0x000"`, `"#FFFFFF"`, `"7fffd4"`)
- RGB/RGBA tuples (e.g. `(255, 255, 255)`, `(255, 255, 255, 0.5)`)
- [RGB/RGBA strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#RGB_colors)
  (e.g. `"rgb(255, 255, 255)"`, `"rgba(255, 255, 255, 0.5)"`)
- [HSL strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#HSL_colors)
  (e.g. `"hsl(270, 60%, 70%)"`, `"hsl(270, 60%, 70%, .5)"`)

```py
{!.tmp_examples/types_color.py!}
```
_(This script is complete, it should run "as is")_

`Color` has the following methods:

**`original`**
: the original string or tuple passed to `Color`

**`as_named`**
: returns a named CSS3 color; fails if the alpha channel is set or no such color exists unless
  `fallback=True` is supplied, in which case it falls back to `as_hex`

**`as_hex`**
: returns a string in the format `#fff` or `#ffffff`; will contain 4 (or 8) hex values if the alpha channel is set,
  e.g. `#7f33cc26`

**`as_rgb`**
: returns a string in the format `rgb(<red>, <green>, <blue>)`, or `rgba(<red>, <green>, <blue>, <alpha>)`
  if the alpha channel is set

**`as_rgb_tuple`**
: returns a 3- or 4-tuple in RGB(a) format. The `alpha` keyword argument can be used to define whether
  the alpha channel should be included;
  options: `True` - always include, `False` - never include, `None` (default) - include if set

**`as_hsl`**
: string in the format `hsl(<hue deg>, <saturation %>, <lightness %>)`
  or `hsl(<hue deg>, <saturation %>, <lightness %>, <alpha>)` if the alpha channel is set

**`as_hsl_tuple`**
: returns a 3- or 4-tuple in HSL(a) format. The `alpha` keyword argument can be used to define whether
  the alpha channel should be included;
  options: `True` - always include, `False` - never include, `None` (the default)  - include if set

The `__str__` method for `Color` returns `self.as_named(fallback=True)`.

!!! note
    the `as_hsl*` refer to hue, saturation, lightness "HSL" as used in html and most of the world, **not**
    "HLS" as used in Python's `colorsys`.

### Secret Types

You can use the `SecretStr` and the `SecretBytes` data types for storing sensitive information
that you do not want to be visible in logging or tracebacks.
`SecretStr` and `SecretBytes` can be initialized idempotently or by using `str` or `bytes` literals respectively.
The `SecretStr` and `SecretBytes` will be formatted as either `'**********'` or `''` on conversion to json.

```py
{!.tmp_examples/types_secret_types.py!}
```
_(This script is complete, it should run "as is")_

### Json Type

You can use `Json` data type to make *pydantic* first load a raw JSON string.
It can also optionally be used to parse the loaded object into another type base on
the type `Json` is parameterised with:

```py
{!.tmp_examples/types_json_type.py!}
```
_(This script is complete, it should run "as is")_

### Payment Card Numbers

The `PaymentCardNumber` type validates [payment cards](https://en.wikipedia.org/wiki/Payment_card)
(such as a debit or credit card).

```py
{!.tmp_examples/types_payment_card_number.py!}
```
_(This script is complete, it should run "as is")_

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

## Constrained Types

The value of numerous common types can be restricted using `con*` type functions:

```py
{!.tmp_examples/types_constrained.py!}
```
_(This script is complete, it should run "as is")_

Where `Field` refers to the [field function](schema.md#field-customisation).

### Arguments to `conlist`
The following arguments are available when using the `conlist` type function

- `item_type: Type[T]`: type of the list items
- `min_items: int = None`: minimum number of items in the list
- `max_items: int = None`: maximum number of items in the list
- `unique_items: bool = None`: enforces list elements to be unique

### Arguments to `conset`
The following arguments are available when using the `conset` type function

- `item_type: Type[T]`: type of the set items
- `min_items: int = None`: minimum number of items in the set
- `max_items: int = None`: maximum number of items in the set

### Arguments to `confrozenset`
The following arguments are available when using the `confrozenset` type function

- `item_type: Type[T]`: type of the frozenset items
- `min_items: int = None`: minimum number of items in the frozenset
- `max_items: int = None`: maximum number of items in the frozenset

### Arguments to `conint`
The following arguments are available when using the `conint` type function

- `strict: bool = False`: controls type coercion
- `gt: int = None`: enforces integer to be greater than the set value
- `ge: int = None`: enforces integer to be greater than or equal to the set value
- `lt: int = None`: enforces integer to be less than the set value
- `le: int = None`: enforces integer to be less than or equal to the set value
- `multiple_of: int = None`: enforces integer to be a multiple of the set value

### Arguments to `confloat`
The following arguments are available when using the `confloat` type function

- `strict: bool = False`: controls type coercion
- `gt: float = None`: enforces float to be greater than the set value
- `ge: float = None`: enforces float to be greater than or equal to the set value
- `lt: float = None`: enforces float to be less than the set value
- `le: float = None`: enforces float to be less than or equal to the set value
- `multiple_of: float = None`: enforces float to be a multiple of the set value

### Arguments to `condecimal`
The following arguments are available when using the `condecimal` type function

- `gt: Decimal = None`: enforces decimal to be greater than the set value
- `ge: Decimal = None`: enforces decimal to be greater than or equal to the set value
- `lt: Decimal = None`: enforces decimal to be less than the set value
- `le: Decimal = None`: enforces decimal to be less than or equal to the set value
- `max_digits: int = None`: maximum number of digits within the decimal. it does not include a zero before the decimal point or trailing decimal zeroes
- `decimal_places: int = None`: max number of decimal places allowed. it does not include trailing decimal zeroes
- `multiple_of: Decimal = None`: enforces decimal to be a multiple of the set value

### Arguments to `constr`
The following arguments are available when using the `constr` type function

- `strip_whitespace: bool = False`: removes leading and trailing whitespace
- `to_upper: bool = False`: turns all characters to uppercase
- `to_lower: bool = False`: turns all characters to lowercase
- `strict: bool = False`: controls type coercion
- `min_length: int = None`: minimum length of the string
- `max_length: int = None`: maximum length of the string
- `curtail_length: int = None`: shrinks the string length to the set value when it is longer than the set value
- `regex: str = None`: regex to validate the string against

### Arguments to `conbytes`
The following arguments are available when using the `conbytes` type function

- `strip_whitespace: bool = False`: removes leading and trailing whitespace
- `to_upper: bool = False`: turns all characters to uppercase
- `to_lower: bool = False`: turns all characters to lowercase
- `min_length: int = None`: minimum length of the byte string
- `max_length: int = None`: maximum length of the byte string
- `strict: bool = False`: controls type coercion


## Strict Types

You can use the `StrictStr`, `StrictBytes`, `StrictInt`, `StrictFloat`, and `StrictBool` types
to prevent coercion from compatible types.
These types will only pass validation when the validated value is of the respective type or is a subtype of that type.
This behavior is also exposed via the `strict` field of the `ConstrainedStr`, `ConstrainedBytes`,
`ConstrainedFloat` and `ConstrainedInt` classes and can be combined with a multitude of complex validation rules.

The following caveats apply:

- `StrictBytes` (and the `strict` option of `ConstrainedBytes`) will accept both `bytes`,
   and `bytearray` types.
- `StrictInt` (and the `strict` option of `ConstrainedInt`) will not accept `bool` types,
    even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `ConstrainedFloat`) will not accept `int`.

```py
{!.tmp_examples/types_strict.py!}
```
_(This script is complete, it should run "as is")_

## ByteSize

You can use the `ByteSize` data type to convert byte string representation to
raw bytes and print out human readable versions of the bytes as well.

!!! info
    Note that `1b` will be parsed as "1 byte" and not "1 bit".

```py
{!.tmp_examples/types_bytesize.py!}
```
_(This script is complete, it should run "as is")_

## Custom Data Types

You can also define your own custom data types. There are several ways to achieve it.

### Classes with `__get_validators__`

You use a custom class with a classmethod `__get_validators__`. It will be called
to get validators to parse and validate the input data.

!!! tip
    These validators have the same semantics as in [Validators](validators.md), you can
    declare a parameter `config`, `field`, etc.

```py
{!.tmp_examples/types_custom_type.py!}
```
_(This script is complete, it should run "as is")_

Similar validation could be achieved using [`constr(regex=...)`](#constrained-types) except the value won't be
formatted with a space, the schema would just include the full pattern and the returned value would be a vanilla string.

See [schema](schema.md) for more details on how the model's schema is generated.

### Arbitrary Types Allowed

You can allow arbitrary types using the `arbitrary_types_allowed` config in the
[Model Config](model_config.md).

```py
{!.tmp_examples/types_arbitrary_allowed.py!}
```
_(This script is complete, it should run "as is")_

### Generic Classes as Types

!!! warning
    This is an advanced technique that you might not need in the beginning. In most of
    the cases you will probably be fine with standard *pydantic* models.

You can use
[Generic Classes](https://docs.python.org/3/library/typing.html#typing.Generic) as
field types and perform custom validation based on the "type parameters" (or sub-types)
with `__get_validators__`.

If the Generic class that you are using as a sub-type has a classmethod
`__get_validators__` you don't need to use `arbitrary_types_allowed` for it to work.

Because you can declare validators that receive the current `field`, you can extract
the `sub_fields` (from the generic class type parameters) and validate data with them.

```py
{!.tmp_examples/types_generics.py!}
```
_(This script is complete, it should run "as is")_
