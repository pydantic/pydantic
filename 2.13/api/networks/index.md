The networks module contains types for common network-related fields.

## MAX_EMAIL_LENGTH

```python
MAX_EMAIL_LENGTH = 2048

```

Maximum length for an email. A somewhat arbitrary but very generous number compared to what is allowed by most implementations.

## UrlConstraints

```python
UrlConstraints(
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    preserve_empty_path: bool | None = None,
)

```

Url constraints.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `max_length` | `int | None` | The maximum length of the url. Defaults to None. | | `allowed_schemes` | `list[str] | None` | The allowed schemes. Defaults to None. | | `host_required` | `bool | None` | Whether the host is required. Defaults to None. | | `default_host` | `str | None` | The default host. Defaults to None. | | `default_port` | `int | None` | The default port. Defaults to None. | | `default_path` | `str | None` | The default path. Defaults to None. | | `preserve_empty_path` | `bool | None` | Whether to preserve empty URL paths. Defaults to None. |

### defined_constraints

```python
defined_constraints: dict[str, Any]

```

Fetch a key / value mapping of constraints to values that are not None. Used for core schema updates.

## AnyUrl

```python
AnyUrl(url: str | Url | _BaseUrl)

```

Bases: `_BaseUrl`

Base type for all URLs.

- Any scheme allowed
- Top-level domain (TLD) not required
- Host not required

Assuming an input URL of `http://samuel:pass@example.com:8000/the/path/?query=here#fragment=is;this=bit`, the types export the following properties:

- `scheme`: the URL scheme (`http`), always set.
- `host`: the URL host (`example.com`).
- `username`: optional username if included (`samuel`).
- `password`: optional password if included (`pass`).
- `port`: optional port (`8000`).
- `path`: optional path (`/the/path/`).
- `query`: optional URL query (for example, `GET` arguments or "search string", such as `query=here`).
- `fragment`: optional fragment (`fragment=is;this=bit`).

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## AnyHttpUrl

```python
AnyHttpUrl(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any http or https URL.

- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## HttpUrl

```python
HttpUrl(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any http or https URL.

- TLD not required
- Host not required
- Max length 2083

```python
from pydantic import BaseModel, HttpUrl, ValidationError

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')  # (1)!
print(m.url)
#> http://www.example.com/

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyModel
    url
      URL scheme should be 'http' or 'https' [type=url_scheme, input_value='ftp://invalid.url', input_type=str]
    '''

try:
    MyModel(url='not a url')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyModel
    url
      Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='not a url', input_type=str]
    '''

```

1. Note: mypy would prefer `m = MyModel(url=HttpUrl('http://www.example.com'))`, but Pydantic will convert the string to an HttpUrl instance anyway.

"International domains" (e.g. a URL where the host or TLD includes non-ascii characters) will be encoded via [punycode](https://en.wikipedia.org/wiki/Punycode) (see [this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```python
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

Underscores in Hostnames

In Pydantic, underscores are allowed in all parts of a domain except the TLD. Technically this might be wrong - in theory the hostname cannot have underscores, but subdomains can.

To explain this; consider the following two cases:

- `exam_ple.co.uk`: the hostname is `exam_ple`, which should not be allowed since it contains an underscore.
- `foo_bar.example.com` the hostname is `example`, which should be allowed since the underscore is in the subdomain.

Without having an exhaustive list of TLDs, it would be impossible to differentiate between these two. Therefore underscores are allowed, but you can always do further validation in a validator if desired.

Also, Chrome, Firefox, and Safari all currently accept `http://exam_ple.com` as a URL, so we're in good (or at least big) company.

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## AnyWebsocketUrl

```python
AnyWebsocketUrl(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any ws or wss URL.

- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## WebsocketUrl

```python
WebsocketUrl(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any ws or wss URL.

- TLD not required
- Host not required
- Max length 2083

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## FileUrl

```python
FileUrl(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any file URL.

- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## FtpUrl

```python
FtpUrl(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept ftp URL.

- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## PostgresDsn

```python
PostgresDsn(url: str | MultiHostUrl | _BaseMultiHostUrl)

```

Bases: `_BaseMultiHostUrl`

A type that will accept any Postgres DSN.

- User info required
- TLD not required
- Host required
- Supports multiple hosts

If further validation is required, these properties can be used by validators to enforce specific behaviour:

```python
from pydantic import (
    BaseModel,
    HttpUrl,
    PostgresDsn,
    ValidationError,
    field_validator,
)

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')

# the repr() method for a url will display all properties of the url
print(repr(m.url))
#> HttpUrl('http://www.example.com/')
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
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyDatabaseModel
    db
      Assertion failed, database must be provided
    assert (None)
     +  where None = PostgresDsn('postgres://user:pass@localhost:5432').path [type=assertion_error, input_value='postgres://user:pass@localhost:5432', input_type=str]
    '''

```

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreMultiHostUrl | _BaseMultiHostUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

### host

```python
host: str

```

The required URL host.

## CockroachDsn

```python
CockroachDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any Cockroach DSN.

- User info required
- TLD not required
- Host required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

### host

```python
host: str

```

The required URL host.

## AmqpDsn

```python
AmqpDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any AMQP DSN.

- User info required
- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## RedisDsn

```python
RedisDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any Redis DSN.

- User info required
- TLD not required
- Host required (e.g., `rediss://:pass@localhost`)

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

### host

```python
host: str

```

The required URL host.

## MongoDsn

```python
MongoDsn(url: str | MultiHostUrl | _BaseMultiHostUrl)

```

Bases: `_BaseMultiHostUrl`

A type that will accept any MongoDB DSN.

- User info not required
- Database name not required
- Port not required
- User info may be passed without user part (e.g., `mongodb://mongodb0.example.com:27017`).

Warning

If a port isn't specified, the default MongoDB port `27017` will be used. If this behavior is undesirable, you can use the following:

```python
from typing import Annotated

from pydantic_core import MultiHostUrl

from pydantic import UrlConstraints

MongoDsnNoDefaultPort = Annotated[
    MultiHostUrl,
    UrlConstraints(allowed_schemes=['mongodb', 'mongodb+srv']),
]

```

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreMultiHostUrl | _BaseMultiHostUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## KafkaDsn

```python
KafkaDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any Kafka DSN.

- User info required
- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## NatsDsn

```python
NatsDsn(url: str | MultiHostUrl | _BaseMultiHostUrl)

```

Bases: `_BaseMultiHostUrl`

A type that will accept any NATS DSN.

NATS is a connective technology built for the ever increasingly hyper-connected world. It is a single technology that enables applications to securely communicate across any combination of cloud vendors, on-premise, edge, web and mobile, and devices. More: https://nats.io

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreMultiHostUrl | _BaseMultiHostUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## MySQLDsn

```python
MySQLDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any MySQL DSN.

- User info required
- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## MariaDBDsn

```python
MariaDBDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any MariaDB DSN.

- User info required
- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## ClickHouseDsn

```python
ClickHouseDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any ClickHouse DSN.

- User info required
- TLD not required
- Host not required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

## SnowflakeDsn

```python
SnowflakeDsn(url: str | Url | _BaseUrl)

```

Bases: `AnyUrl`

A type that will accept any Snowflake DSN.

- User info required
- TLD not required
- Host required

Source code in `pydantic/networks.py`

```python
def __init__(self, url: str | _CoreUrl | _BaseUrl) -> None:
    self._url = _build_type_adapter(self.__class__).validate_python(url)._url

```

### host

```python
host: str

```

The required URL host.

## EmailStr

Info

To use this type, you need to install the optional [`email-validator`](https://github.com/JoshData/python-email-validator) package:

```bash
pip install email-validator

```

Validate email addresses.

```python
from pydantic import BaseModel, EmailStr

class Model(BaseModel):
    email: EmailStr

print(Model(email='contact@mail.com'))
#> email='contact@mail.com'

```

## NameEmail

```python
NameEmail(name: str, email: str)

```

Bases: `Representation`

Info

To use this type, you need to install the optional [`email-validator`](https://github.com/JoshData/python-email-validator) package:

```bash
pip install email-validator

```

Validate a name and email address combination, as specified by [RFC 5322](https://datatracker.ietf.org/doc/html/rfc5322#section-3.4).

The `NameEmail` has two properties: `name` and `email`. In case the `name` is not provided, it's inferred from the email address.

```python
from pydantic import BaseModel, NameEmail

class User(BaseModel):
    email: NameEmail

user = User(email='Fred Bloggs <fred.bloggs@example.com>')
print(user.email)
#> Fred Bloggs <fred.bloggs@example.com>
print(user.email.name)
#> Fred Bloggs

user = User(email='fred.bloggs@example.com')
print(user.email)
#> fred.bloggs <fred.bloggs@example.com>
print(user.email.name)
#> fred.bloggs

```

Source code in `pydantic/networks.py`

```python
def __init__(self, name: str, email: str):
    self.name = name
    self.email = email

```

## IPvAnyAddress

Validate an IPv4 or IPv6 address.

```python
from pydantic import BaseModel
from pydantic.networks import IPvAnyAddress

class IpModel(BaseModel):
    ip: IPvAnyAddress

print(IpModel(ip='127.0.0.1'))
#> ip=IPv4Address('127.0.0.1')

try:
    IpModel(ip='http://www.example.com')
except ValueError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'ip_any_address',
            'loc': ('ip',),
            'msg': 'value is not a valid IPv4 or IPv6 address',
            'input': 'http://www.example.com',
        }
    ]
    '''

```

## IPvAnyInterface

Validate an IPv4 or IPv6 interface.

## IPvAnyNetwork

Validate an IPv4 or IPv6 network.

## validate_email

```python
validate_email(value: str) -> tuple[str, str]

```

Email address validation using [email-validator](https://pypi.org/project/email-validator/).

Returns:

| Type | Description | | --- | --- | | `tuple[str, str]` | A tuple containing the local part of the email (or the name for "pretty" email addresses) and the normalized email. |

Raises:

| Type | Description | | --- | --- | | `PydanticCustomError` | If the email is invalid. |

Note

Note that:

- Raw IP address (literal) domain parts are not allowed.
- `"John Doe <local_part@domain.com>"` style "pretty" email addresses are processed.
- Spaces are striped from the beginning and end of addresses, but no error is raised.

Source code in `pydantic/networks.py`

```python
def validate_email(value: str) -> tuple[str, str]:
    """Email address validation using [email-validator](https://pypi.org/project/email-validator/).

    Returns:
        A tuple containing the local part of the email (or the name for "pretty" email addresses)
            and the normalized email.

    Raises:
        PydanticCustomError: If the email is invalid.

    Note:
        Note that:

        * Raw IP address (literal) domain parts are not allowed.
        * `"John Doe <local_part@domain.com>"` style "pretty" email addresses are processed.
        * Spaces are striped from the beginning and end of addresses, but no error is raised.
    """
    if email_validator is None:
        import_email_validator()

    if len(value) > MAX_EMAIL_LENGTH:
        raise PydanticCustomError(
            'value_error',
            'value is not a valid email address: {reason}',
            {'reason': f'Length must not exceed {MAX_EMAIL_LENGTH} characters'},
        )

    m = pretty_email_regex.fullmatch(value)
    name: str | None = None
    if m:
        unquoted_name, quoted_name, value = m.groups()
        name = unquoted_name or quoted_name

    email = value.strip()

    try:
        parts = email_validator.validate_email(email, check_deliverability=False)
    except email_validator.EmailNotValidError as e:
        raise PydanticCustomError(
            'value_error', 'value is not a valid email address: {reason}', {'reason': str(e.args[0])}
        ) from e

    email = parts.normalized
    assert email is not None
    name = name or parts.local_part
    return name, email

```
