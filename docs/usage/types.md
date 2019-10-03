**TODO intro to types**.

## Standard iterable types

*pydantic* uses standard library `typing` types to define complex objects.

```py
{!./examples/ex_typing.py!}
```

(This script is complete, it should run "as is")

## Unions

Example of `Union` usage

### Unions and Type Order

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


## Enums and Choices

*pydantic* uses python's standard `enum` classes to define choices.

```py
{!./examples/choices.py!}
```

(This script is complete, it should run "as is")


## Datetime Types

*Pydantic* supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
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

## Exotic Types

*Pydantic* comes with a number of utilities for parsing or validating common objects.

```py
{!./examples/exotic.py!}
```

(This script is complete, it should run "as is")

## Booleans

!!! warning
    The logic for parsing `bool` fields has changed as of version **v1.0**.

    Prior to **v1.0**, `bool` parsing never failed, leading to some unexpected results.
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

## Callable

Fields can also be of type `Callable`:

```py
{!./examples/callable.py!}
```

(This script is complete, it should run "as is")

!!! warning
    Callable fields only perform a simple check that the argument is
    callable, no validation of arguments, their types or the return
    type is performed.

## URLs

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

### URL Properties

Assuming an input URL of `http://samuel:pass@example.com:8000/the/path/?query=here#fragment=is;this=bit`,
the above types export the following properties:

- `scheme`: always set - the url schema e.g. `http` above
- `host`: always set - the url host e.g. `example.com` above
- `host_type`: always set - describes the type of host, either:

  - `domain`: e.g. for `example.com`,
  - `int_domain`: international domain, see [below](#international-domains), e.g. for `exampl£e.org`,
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

### International Domains

"International domains" (e.g. a URL where the host includes non-ascii characters) will be encode via
[punycode](https://en.wikipedia.org/wiki/Punycode) (see
[this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```py
{!./examples/url_punycode.py!}
```

(This script is complete, it should run "as is")

### Underscores in Hostnames

!!! note
    In *pydantic* underscores are allowed in all parts of a domain except the tld.
    Technically this might be wrong - in theory the hostname cannot have underscores but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk` hostname is `exam_ple`, should not be allowed as there's an underscore in there
    - `foo_bar.example.com` hostname is `example` should be allowed since the underscore is in the subdomain

    Without having an exhaustive list of TLDs it would be impossible to differentiate between these two. Therefore
    underscores are allowed, you could do further validation in a validator if you wanted.

    Also, chrome currently accepts `http://exam_ple.com` as a URL, so we're in good (or at least big) company.

## Color Type

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

**`original`**
: the original string or tuple passed to `Color`

**`as_named`**
: returns a named CSS3 color, fails if the alpha channel is set or no such color exists unless
  `fallback=True` is supplied when it falls back to `as_hex`

**`as_hex`**
: string in the format `#ffffff` or `#fff`, can also be a 4 or 8 hex values if the alpha channel is set,
  e.g. `#7f33cc26`

**`as_rgb`**
: string in the format `rgb(<red>, <green>, <blue>)` or `rgba(<red>, <green>, <blue>, <alpha>)`
  if the alpha channel is set

**`as_rgb_tuple`**
: returns a 3- or 4-tuple in RGB(a) format, the `alpha` keyword argument can be used to define whether
  the alpha channel should be included,
  options: `True` - always include, `False` - never include, `None` (the default) - include if set

**`as_hsl`**
: string in the format `hsl(<hue deg>, <saturation %>, <lightness %>)`
  or `hsl(<hue deg>, <saturation %>, <lightness %>, <alpha>)` if the alpha channel is set

**`as_hsl_tuple`**
: returns a 3- or 4-tuple in HSL(a) format, the `alpha` keyword argument can be used to define whether
  the alpha channel should be included,
  options: `True` - always include, `False` - never include, `None` (the default)  - include if set

The `__str__` method for `Color` returns `self.as_named(fallback=True)`.

!!! note
    the `as_hsl*` refer to hue, saturation, lightness "HSL" as used in html and most of the world, **not**
    "HLS" as used in python's `colorsys`.

## Secret Types

You can use the `SecretStr` and the `SecretBytes` data types for storing sensitive information
that you do not want to be visible in logging or tracebacks.
The SecretStr and SecretBytes will be formatted as either `'**********'` or `''` on conversion to json.

```py
{!./examples/ex_secret_types.py!}
```

(This script is complete, it should run "as is")

## Strict Types

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

## Json Type

You can use `Json` data type - *Pydantic* will first parse raw JSON string and then will validate parsed object
against defined Json structure if it's provided.

```py
{!./examples/ex_json_type.py!}
```

(This script is complete, it should run "as is")

## Literal Type

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

## Payment Card Numbers

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

## Type Type

Pydantic supports the use of `Type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

```py
{!./examples/type_type.py!}
```

You may also use `Type` to specify that any class is allowed.

```py
{!./examples/bare_type_type.py!}
```

## Custom Data Types

You can also define your own data types. The class method `__get_validators__` will be called
to get validators to parse and validate the input data.

```py
{!./examples/custom_data_types.py!}
```

(This script is complete, it should run "as is")
