

For URI/URL validation the following types are available:

- [`AnyUrl`][pydantic.networks.AnyUrl]: any scheme allowed, top-level domain (TLD) not required, host required.
- [`AnyHttpUrl`][pydantic.networks.AnyHttpUrl]: scheme `http` or `https`, TLD not required, host required.
- [`HttpUrl`][pydantic.networks.HttpUrl]: scheme `http` or `https`, TLD required, host required, max length 2083.
- [`FileUrl`][pydantic.networks.FileUrl]: scheme `file`, host not required.
- [`PostgresDsn`][pydantic.networks.PostgresDsn]: user info required, TLD not required, host required.
    `PostgresDsn` supports multiple hosts. The following schemes are supported:
    - `postgres`
    - `postgresql`
    - `postgresql+asyncpg`
    - `postgresql+pg8000`
    - `postgresql+psycopg`
    - `postgresql+psycopg2`
    - `postgresql+psycopg2cffi`
    - `postgresql+py-postgresql`
    - `postgresql+pygresql`
- [`MySQLDsn`][pydantic.networks.MySQLDsn]: scheme `mysql`, user info required, TLD not required, host required.
    Also, its supported DBAPI dialects:
    - `mysql`
    - `mysql+mysqlconnector`
    - `mysql+aiomysql`
    - `mysql+asyncmy`
    - `mysql+mysqldb`
    - `mysql+pymysql`
    - `mysql+cymysql`
    - `mysql+pyodbc`
- [`MariaDBDsn`][pydantic.networks.MariaDBDsn]: scheme `mariadb`, user info required, TLD not required, host required.
    Also, its supported DBAPI dialects:
    - `mariadb`
    - `mariadb+mariadbconnector`
    - `mariadb+pymysql`
- [`CockroachDsn`][pydantic.networks.CockroachDsn]: scheme `cockroachdb`, user info required, TLD not required,
    host required. Also, its supported DBAPI dialects:
    - `cockroachdb+asyncpg`
    - `cockroachdb+psycopg2`
- [`AmqpDsn`][pydantic.networks.AmqpDsn]: schema `amqp` or `amqps`, user info not required, TLD not required,
    host not required.
- [`RedisDsn`][pydantic.networks.RedisDsn]: scheme `redis` or `rediss`, user info not required, TLD not required,
    host not required (e.g., `rediss://:pass@localhost`).
- [`MongoDsn`][pydantic.networks.MongoDsn]: scheme `mongodb`, user info not required, database name not required, port
    not required, user info may be passed without user part
    (e.g., `mongodb://mongodb0.example.com:27017`).

The above types (which all inherit from [`AnyUrl`][pydantic.networks.AnyUrl]) will attempt to give descriptive
errors when invalid URLs are provided:

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

- `scheme`: the URL scheme (`http`), always set.
- `host`: the URL host (`example.com`), always set.
- `username`: optional username if included (`samuel`).
- `password`: optional password if included (`pass`).
- `port`: optional port (`8000`).
- `path`: optional path (`/the/path/`).
- `query`: optional URL query (for example, `GET` arguments or "search string", such as `query=here`).
- `fragment`: optional fragment (`fragment=is;this=bit`).

If further validation is required, these properties can be used by validators to enforce specific behaviour:

```py
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
except ValidationError as e:
    print(e)
    """
    1 validation error for MyDatabaseModel
    db
      Assertion failed, database must be provided
    assert (None)
     +  where None = MultiHostUrl('postgres://user:pass@localhost:5432').path [type=assertion_error, input_value='postgres://user:pass@localhost:5432', input_type=str]
    """
```

#### International domains

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


!!! warning "Underscores in Hostnames"
    In Pydantic, underscores are allowed in all parts of a domain except the TLD.
    Technically this might be wrong - in theory the hostname cannot have underscores, but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk`: the hostname is `exam_ple`, which should not be allowed since it contains an underscore.
    - `foo_bar.example.com` the hostname is `example`, which should be allowed since the underscore is in the subdomain.

    Without having an exhaustive list of TLDs, it would be impossible to differentiate between these two. Therefore
    underscores are allowed, but you can always do further validation in a validator if desired.

    Also, Chrome, Firefox, and Safari all currently accept `http://exam_ple.com` as a URL, so we're in good
    (or at least big) company.

## IP Addresses

Pydantic provides types for IP addresses and networks, which support the standard library
IP address, interface, and network types.

- [`IPvAnyAddress`][pydantic.networks.IPvAnyAddress]: allows either an `IPv4Address` or an `IPv6Address`.
- [`IPvAnyInterface`][pydantic.networks.IPvAnyInterface]: allows either an `IPv4Interface` or an `IPv6Interface`.
- [`IPvAnyNetwork`][pydantic.networks.IPvAnyNetwork]: allows either an `IPv4Network` or an `IPv6Network`.

```py
from pydantic import BaseModel
from pydantic.networks import IPvAnyAddress


class IpModel(BaseModel):
    ip: IPvAnyAddress


print(IpModel(ip='127.0.0.1'))
#> ip=IPv4Address('127.0.0.1')

try:
    IpModel(ip='http://www.example.com')
except ValueError as e:
    print(e)
    """
    1 validation error for IpModel
    ip
      value is not a valid IPv4 or IPv6 address [type=ip_any_address, input_value='http://www.example.com', input_type=str]
    """
```
