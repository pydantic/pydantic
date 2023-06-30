

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


!!! warning "Underscores in Hostnames"
    In Pydantic underscores are allowed in all parts of a domain except the tld.
    Technically this might be wrong - in theory the hostname cannot have underscores, but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk`: the hostname is `exam_ple`, which should not be allowed since it contains an underscore
    - `foo_bar.example.com` the hostname is `example`, which should be allowed since the underscore is in the subdomain

    Without having an exhaustive list of TLDs, it would be impossible to differentiate between these two. Therefore
    underscores are allowed, but you can always do further validation in a validator if desired.

    Also, Chrome, Firefox, and Safari all currently accept `http://exam_ple.com` as a URL, so we're in good
    (or at least big) company.

## IP Addresses

`IPvAnyAddress`
: allows either an `IPv4Address` or an `IPv6Address`

`IPvAnyInterface`
: allows either an `IPv4Interface` or an `IPv6Interface`

`IPvAnyNetwork`
: allows either an `IPv4Network` or an `IPv6Network`
