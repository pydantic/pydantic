Where possible *pydantic* uses [standard library types](/usage/standard_types/#standard-library-types) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so *pydantic* implements [many commonly used types](/usage/pydantic_types/#pydantic-types).

If no existing type suits your purpose you can also implement your [own pydantic-compatible types](/usage/custom/#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.

* [Standard Library Types](/usage/standard_types/)
* [Typing Iterables](/usage/typing_iterables/) ;emdash; iterable `typing` types including `Deque`, `Dict`, `FrozenSet`, `List`, `Optional`, `Sequence`, `Set`, and `Tuple`.
* [Unions](/usage/unions/) ;emdash; allows a model attribute to accept different types.
* [Enums and Choices](/usage/enums/) ;emdash; uses Python's standard `enum` classes to define choices.
* [Datetime Types](/usage/datetimes/) ;emdash; `datetime`, `date`, `time`, and `timedelta` types.
* [Booleans](/usage/booleans/) ;emdash; `bool` types.
* [Callable](/usage/callable/) ;emdash; `Callable` types.
* [Type and TypeVar](/usage/typevars/) ;emdash; `Type` and `TypeVar` types.
* [Literal](/usage/literals/) ;emdash; `Literal` types.
* [Annotated Types](/usage/annotated_types/) ;emdash; `Annotated` types, including `NamedTuple` and `TypedDict`.
* [Pydantic Types](/usage/pydantic_types/) ;emdash; general types provided by Pydantic.
* [ImportString](/usage/importstring/) ;emdash; a type that references a Python module or object by string name.
* [URLs](/usage/urls/) ;emdash; URI/URL validation types.

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
  - `postgresql+psycopg`
  - `postgresql+psycopg2`
  - `postgresql+psycopg2cffi`
  - `postgresql+py-postgresql`
  - `postgresql+pygresql`
- `MySQLDsn`: scheme `mysql`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `mysql`
  - `mysql+mysqlconnector`
  - `mysql+aiomysql`
  - `mysql+asyncmy`
  - `mysql+mysqldb`
  - `mysql+pymysql`
  - `mysql+cymysql`
  - `mysql+pyodbc`
- `MariaDBDsn`: scheme `mariadb`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `mariadb`
  - `mariadb+mariadbconnector`
  - `mariadb+pymysql`
- `CockroachDsn`: scheme `cockroachdb`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `cockroachdb+asyncpg`
  - `cockroachdb+psycopg2`
- `AmqpDsn`: schema `amqp` or `amqps`, user info not required, TLD not required, host not required
- `RedisDsn`: scheme `redis` or `rediss`, user info not required, tld not required, host not required (CHANGED: user info) (e.g., `rediss://:pass@localhost`)
- `MongoDsn` : scheme `mongodb`, user info not required, database name not required, port
  not required from **v1.6** onwards), user info may be passed without user part (e.g., `mongodb://mongodb0.example.com:27017`)
- `stricturl`: method with the following keyword arguments:
    - `strip_whitespace: bool = True`
    - `min_length: int = 1`
    - `max_length: int = 2 ** 16`
    - `tld_required: bool = True`
    - `host_required: bool = True`
    - `allowed_schemes: Optional[Set[str]] = None`

!!! warning
    In V1.10.0 and v1.10.1 `stricturl` also took an optional `quote_plus` argument and URL components were percent
    encoded in some cases. This feature was removed in v1.10.2, see
    [#4470](https://github.com/pydantic/pydantic/pull/4470) for explanation and more details.

The above types (which all inherit from `AnyUrl`) will attempt to give descriptive errors when invalid URLs are
provided:

```py
from pydantic import BaseModel, HttpUrl, ValidationError


class MyModel(BaseModel):
    url: HttpUrl


m = MyModel(url='http://www.example.com')
print(m.url)
#> http://www.example.com/

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    url
      URL scheme should be 'http' or 'https' [type=url_scheme, input_value='ftp://invalid.url', input_type=str]
    """

try:
    MyModel(url='not a url')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    url
      Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='not a url', input_type=str]
    """
```

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
from pydantic import BaseModel, HttpUrl, PostgresDsn, ValidationError, field_validator


class MyModel(BaseModel):
    url: HttpUrl


m = MyModel(url='http://www.example.com')

# the repr() method for a url will display all properties of the url
print(repr(m.url))
#> Url('http://www.example.com/')
print(m.url.scheme)
#> http
print(m.url.host)
#> www.example.com
print(m.url.port)
#> 80


class MyDatabaseModel(BaseModel):
    db: PostgresDsn

    @field_validator('db')
    def check_db_name(cls, v):
        assert v.path and len(v.path) > 1, 'database must be provided'
        return v


m = MyDatabaseModel(db='postgres://user:pass@localhost:5432/foobar')
print(m.db)
#> postgres://user:pass@localhost:5432/foobar

try:
    MyDatabaseModel(db='postgres://user:pass@localhost:5432')
except ValidationError:
    pass
    # TODO the error output here is wrong!
    # print(e)
```

#### International Domains

"International domains" (e.g. a URL where the host or TLD includes non-ascii characters) will be encoded via
[punycode](https://en.wikipedia.org/wiki/Punycode) (see
[this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```py
from pydantic import BaseModel, HttpUrl


class MyModel(BaseModel):
    url: HttpUrl


m1 = MyModel(url='http://puny£code.com')
print(m1.url)
#> http://xn--punycode-eja.com/
m2 = MyModel(url='https://www.аррӏе.com/')
print(m2.url)
#> https://www.xn--80ak6aa92e.com/
m3 = MyModel(url='https://www.example.珠宝/')
print(m3.url)
#> https://www.example.xn--pbt977c/
```


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
from pydantic import BaseModel, ValidationError
from pydantic.color import Color

c = Color('ff00ff')
print(c.as_named())
#> magenta
print(c.as_hex())
#> #f0f
c2 = Color('green')
print(c2.as_rgb_tuple())
#> (0, 128, 0)
print(c2.original())
#> green
print(repr(Color('hsl(180, 100%, 50%)')))
#> Color('cyan', rgb=(0, 255, 255))


class Model(BaseModel):
    color: Color


print(Model(color='purple'))
#> color=Color('purple', rgb=(128, 0, 128))
try:
    Model(color='hello')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    color
      value is not a valid color: string not recognised as a valid color [type=color_error, input_value='hello', input_type=str]
    """
```

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

```py test="xfail - replace json_encoders"
from pydantic import BaseModel, SecretBytes, SecretStr, ValidationError


class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes


sm = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm)
print(sm.password)
print(sm.model_dump())
print(sm.model_dump_json())

# Use get_secret_value method to see the secret's content.
print(sm.password.get_secret_value())
print(sm.password_bytes.get_secret_value())

try:
    SimpleModel(password=[1, 2, 3], password_bytes=[1, 2, 3])
except ValidationError as e:
    print(e)


# If you want the secret to be dumped as plain-text using the json method,
# you can use json_encoders in the Config class.
class SimpleModelDumpable(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
            SecretBytes: lambda v: v.get_secret_value() if v else None,
        }


sm2 = SimpleModelDumpable(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm2)
print(sm2.password)
print(sm2.model_dump())

# But the json method will
print(sm2.model_dump_json())
```

### Json Type

You can use `Json` data type to make *pydantic* first load a raw JSON string.
It can also optionally be used to parse the loaded object into another type base on
the type `Json` is parameterised with:

```py
from typing import Any, List

from pydantic import BaseModel, Json, ValidationError


class AnyJsonModel(BaseModel):
    json_obj: Json[Any]


class ConstrainedJsonModel(BaseModel):
    json_obj: Json[List[int]]


print(AnyJsonModel(json_obj='{"b": 1}'))
#> json_obj={'b': 1}
print(ConstrainedJsonModel(json_obj='[1, 2, 3]'))
#> json_obj=[1, 2, 3]
try:
    ConstrainedJsonModel(json_obj=12)
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedJsonModel
    json_obj
      JSON input should be string, bytes or bytearray [type=json_type, input_value=12, input_type=int]
    """

try:
    ConstrainedJsonModel(json_obj='[a, b]')
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedJsonModel
    json_obj
      Invalid JSON: expected value at line 1 column 2 [type=json_invalid, input_value='[a, b]', input_type=str]
    """

try:
    ConstrainedJsonModel(json_obj='["a", "b"]')
except ValidationError as e:
    print(e)
    """
    2 validation errors for ConstrainedJsonModel
    json_obj -> 0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    json_obj -> 1
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='b', input_type=str]
    """
```

### Payment Card Numbers

The `PaymentCardNumber` type validates [payment cards](https://en.wikipedia.org/wiki/Payment_card)
(such as a debit or credit card).

```py
from datetime import date

from pydantic import BaseModel
from pydantic.types import PaymentCardBrand, PaymentCardNumber, constr


class Card(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    number: PaymentCardNumber
    exp: date

    @property
    def brand(self) -> PaymentCardBrand:
        return self.number.brand

    @property
    def expired(self) -> bool:
        return self.exp < date.today()


card = Card(
    name='Georg Wilhelm Friedrich Hegel',
    number='4000000000000002',
    exp=date(2023, 9, 30),
)

assert card.number.brand == PaymentCardBrand.visa
assert card.number.bin == '400000'
assert card.number.last4 == '0002'
assert card.number.masked == '400000******0002'
```

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
from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PositiveFloat,
    PositiveInt,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    conset,
    constr,
)


class Model(BaseModel):
    short_bytes: conbytes(min_length=2, max_length=10)
    strict_bytes: conbytes(strict=True)

    upper_str: constr(to_upper=True)
    lower_str: constr(to_lower=True)
    short_str: constr(min_length=2, max_length=10)
    regex_str: constr(pattern=r'^apple (pie|tart|sandwich)$')
    strip_str: constr(strip_whitespace=True)

    big_int: conint(gt=1000, lt=1024)
    mod_int: conint(multiple_of=5)
    pos_int: PositiveInt
    neg_int: NegativeInt
    non_neg_int: NonNegativeInt
    non_pos_int: NonPositiveInt

    big_float: confloat(gt=1000, lt=1024)
    unit_interval: confloat(ge=0, le=1)
    mod_float: confloat(multiple_of=0.5)
    pos_float: PositiveFloat
    neg_float: NegativeFloat
    non_neg_float: NonNegativeFloat
    non_pos_float: NonPositiveFloat

    short_list: conlist(int, min_length=1, max_length=4)
    short_set: conset(int, min_length=1, max_length=4)

    decimal_positive: condecimal(gt=0)
    decimal_negative: condecimal(lt=0)
    decimal_max_digits_and_places: condecimal(max_digits=2, decimal_places=2)
    mod_decimal: condecimal(multiple_of=Decimal('0.25'))

    bigger_int: int = Field(..., gt=10000)
```

Where `Field` refers to the [field function](schema.md#field-customization).

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
- `allow_inf_nan: bool = True`: whether to allows infinity (`+inf` an `-inf`) and NaN values, defaults to `True`,
  set to `False` for compatibility with `JSON`,
  see [#3994](https://github.com/pydantic/pydantic/pull/3994) for more details, added in **V1.10**

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

### Arguments to `condate`
The following arguments are available when using the `condate` type function

- `gt: date = None`: enforces date to be greater than the set value
- `ge: date = None`: enforces date to be greater than or equal to the set value
- `lt: date = None`: enforces date to be less than the set value
- `le: date = None`: enforces date to be less than or equal to the set value


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
from pydantic import (
    BaseModel,
    StrictBool,
    StrictBytes,
    StrictInt,
    ValidationError,
    confloat,
)


class StrictBytesModel(BaseModel):
    strict_bytes: StrictBytes


try:
    StrictBytesModel(strict_bytes='hello world')
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictBytesModel
    strict_bytes
      Input should be a valid bytes [type=bytes_type, input_value='hello world', input_type=str]
    """


class StrictIntModel(BaseModel):
    strict_int: StrictInt


try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictIntModel
    strict_int
      Input should be a valid integer [type=int_type, input_value=3.14159, input_type=float]
    """


class ConstrainedFloatModel(BaseModel):
    constrained_float: confloat(strict=True, ge=0.0)


try:
    ConstrainedFloatModel(constrained_float=3)
except ValidationError as e:
    print(e)

try:
    ConstrainedFloatModel(constrained_float=-1.23)
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedFloatModel
    constrained_float
      Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-1.23, input_type=float]
    """


class StrictBoolModel(BaseModel):
    strict_bool: StrictBool


try:
    StrictBoolModel(strict_bool='False')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for StrictBoolModel
    strict_bool
      Input should be a valid boolean [type=bool_type, input_value='False', input_type=str]
    """
```

## ByteSize

You can use the `ByteSize` data type to convert byte string representation to
raw bytes and print out human readable versions of the bytes as well.

!!! info
    Note that `1b` will be parsed as "1 byte" and not "1 bit".

```py
from pydantic import BaseModel, ByteSize


class MyModel(BaseModel):
    size: ByteSize


print(MyModel(size=52000).size)
#> 52000
print(MyModel(size='3000 KiB').size)
#> 3072000

m = MyModel(size='50 PB')
print(m.size.human_readable())
#> 44.4PiB
print(m.size.human_readable(decimal=True))
#> 50.0PB

print(m.size.to('TiB'))
#> 45474.73508864641
```

## Custom Data Types

You can also define your own custom data types. There are several ways to achieve it.

### Classes with `__get_validators__`

You use a custom class with a classmethod `__get_validators__`. It will be called
to get validators to parse and validate the input data.

!!! tip
    These validators have the same semantics as in [Validators](validators.md), you can
    declare a parameter `config`, `field`, etc.

```py test="xfail - replace with Annoated[str, PostCodeLogic]"
import re

from pydantic import BaseModel

# https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom#Validation
post_code_regex = re.compile(
    r'(?:'
    r'([A-Z]{1,2}[0-9][A-Z0-9]?|ASCN|STHL|TDCU|BBND|[BFS]IQQ|PCRN|TKCA) ?'
    r'([0-9][A-Z]{2})|'
    r'(BFPO) ?([0-9]{1,4})|'
    r'(KY[0-9]|MSR|VG|AI)[ -]?[0-9]{4}|'
    r'([A-Z]{2}) ?([0-9]{2})|'
    r'(GE) ?(CX)|'
    r'(GIR) ?(0A{2})|'
    r'(SAN) ?(TA1)'
    r')'
)


class PostCode(str):
    """
    Partial UK postcode validation. Note: this is just an example, and is not
    intended for use in production; in particular this does NOT guarantee
    a postcode exists, just that it has a valid format.
    """

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __pydantic_modify_json_schema__(cls, field_schema):
        # __pydantic_modify_json_schema__ should mutate the dict it receives
        # in place, the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern='^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
            # some example postcodes
            examples=['SP11 9DG', 'w1j7bu'],
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        m = post_code_regex.fullmatch(v.upper())
        if not m:
            raise ValueError('invalid postcode format')
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(f'{m.group(1)} {m.group(2)}')

    def __repr__(self):
        return f'PostCode({super().__repr__()})'


class Model(BaseModel):
    post_code: PostCode


model = Model(post_code='sw8 5el')
print(model)
print(model.post_code)
print(Model.model_json_schema())
```

Similar validation could be achieved using [`constr(regex=...)`](#constrained-types) except the value won't be
formatted with a space, the schema would just include the full pattern and the returned value would be a vanilla string.

See [schema](schema.md) for more details on how the model's schema is generated.

### Arbitrary Types Allowed

You can allow arbitrary types using the `arbitrary_types_allowed` config in the
[Model Config](model_config.md).

```py
from pydantic import BaseModel, ValidationError


# This is not a pydantic model, it's an arbitrary class
class Pet:
    def __init__(self, name: str):
        self.name = name


class Model(BaseModel):
    model_config = dict(arbitrary_types_allowed=True)
    pet: Pet
    owner: str


pet = Pet(name='Hedwig')
# A simple check of instance type is used to validate the data
model = Model(owner='Harry', pet=pet)
print(model)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model.pet.name)
#> Hedwig
print(type(model.pet))
#> <class '__main__.Pet'>
try:
    # If the value is not an instance of the type, it's invalid
    Model(owner='Harry', pet='Hedwig')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet
      Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
    """
# Nothing in the instance of the arbitrary type is checked
# Here name probably should have been a str, but it's not validated
pet2 = Pet(name=42)
model2 = Model(owner='Harry', pet=pet2)
print(model2)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model2.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model2.pet.name)
#> 42
print(type(model2.pet))
#> <class '__main__.Pet'>
```

### Undefined Types Warning

You can suppress the Undefined Types Warning by setting `undefined_types_warning` to `False` in the
[Model Config](model_config.md).

```py test="xfail - what do we do with undefined_types_warning?"
from __future__ import annotations

from pydantic import BaseModel

# This example shows how Book and Person types reference each other.
# We will demonstrate how to suppress the undefined types warning
# when define such models.


class Book(BaseModel):
    title: str
    author: Person  # note the `Person` type is not yet defined

    # Suppress undefined types warning so we can continue defining our models.
    class Config:
        undefined_types_warning = False


class Person(BaseModel):
    name: str
    books_read: list[Book] | None = None


# Now, we can rebuild the `Book` model, since the `Person` model is now defined.
# Note: there's no need to call `model_rebuild()` on `Person`,
# it's already complete.
Book.model_rebuild()

# Let's create some instances of our models, to demonstrate that they work.
python_crash_course = Book(
    title='Python Crash Course',
    author=Person(name='Eric Matthes'),
)
jane_doe = Person(name='Jane Doe', books_read=[python_crash_course])

assert jane_doe.dict(exclude_unset=True) == {
    'name': 'Jane Doe',
    'books_read': [
        {
            'title': 'Python Crash Course',
            'author': {'name': 'Eric Matthes'},
        },
    ],
}
```

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

```py test="xfail - what do we do with generic custom types"
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField

AgedType = TypeVar('AgedType')
QualityType = TypeVar('QualityType')


# This is not a pydantic model, it's an arbitrary generic class
class TastingModel(Generic[AgedType, QualityType]):
    def __init__(self, name: str, aged: AgedType, quality: QualityType):
        self.name = name
        self.aged = aged
        self.quality = quality

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def validate(cls, v, field: ModelField):
        if not isinstance(v, cls):
            # The value is not even a TastingModel
            raise TypeError('Invalid value')
        if not field.sub_fields:
            # Generic parameters were not provided so we don't try to validate
            # them and just return the value as is
            return v
        aged_f = field.sub_fields[0]
        quality_f = field.sub_fields[1]
        errors = []
        # Here we don't need the validated value, but we want the errors
        valid_value, error = aged_f.validate(v.aged, {}, loc='aged')
        if error:
            errors.append(error)
        # Here we don't need the validated value, but we want the errors
        valid_value, error = quality_f.validate(v.quality, {}, loc='quality')
        if error:
            errors.append(error)
        if errors:
            raise ValidationError(errors, cls)
        # Validation passed without errors, return the same instance received
        return v


class Model(BaseModel):
    # for wine, "aged" is an int with years, "quality" is a float
    wine: TastingModel[int, float]
    # for cheese, "aged" is a bool, "quality" is a str
    cheese: TastingModel[bool, str]
    # for thing, "aged" is a Any, "quality" is Any
    thing: TastingModel


model = Model(
    # This wine was aged for 20 years and has a quality of 85.6
    wine=TastingModel(name='Cabernet Sauvignon', aged=20, quality=85.6),
    # This cheese is aged (is mature) and has "Good" quality
    cheese=TastingModel(name='Gouda', aged=True, quality='Good'),
    # This Python thing has aged "Not much" and has a quality "Awesome"
    thing=TastingModel(name='Python', aged='Not much', quality='Awesome'),
)
print(model)
print(model.wine.aged)
print(model.wine.quality)
print(model.cheese.aged)
print(model.cheese.quality)
print(model.thing.aged)
try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        # For wine, aged should be an int with the years, and quality a float
        wine=TastingModel(name='Merlot', aged=True, quality='Kinda good'),
        # For cheese, aged should be a bool, and quality a str
        cheese=TastingModel(name='Gouda', aged='yeah', quality=5),
        # For thing, no type parameters are declared, and we skipped validation
        # in those cases in the Assessment.validate() function
        thing=TastingModel(name='Python', aged='Not much', quality='Awesome'),
    )
except ValidationError as e:
    print(e)
```
