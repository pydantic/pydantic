---
description: Useful types provided by Pydantic.
---

*pydantic* also provides a variety of other useful types:

`FilePath`
: like `Path`, but the path must exist and be a file

`DirectoryPath`
: like `Path`, but the path must exist and be a directory

`PastDate`
: like `date`, but the date should be in the past

`FutureDate`
: like `date`, but the date should be in the future

`AwareDatetime`
: like `datetime`, but requires the value to have timezone info

`NaiveDatetime`
: like `datetime`, but requires the value to lack timezone info

`EmailStr`
: requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed;
  the input string must be a valid email address, and the output is a simple string



`NameEmail`
: requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed;
  the input string must be either a valid email address or in the format `Fred Bloggs <fred.bloggs@example.com>`,
  and the output is a `NameEmail` object which has two properties: `name` and `email`.
  For `Fred Bloggs <fred.bloggs@example.com>` the name would be `"Fred Bloggs"`;
  for `fred.bloggs@example.com` it would be `"fred.bloggs"`.


`ImportString`
: expects a string and loads the Python object importable at that dotted path; e.g. if `'math.cos'` was provided,
the resulting field value would be the function `cos`; see [ImportString](#importstring)


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

`MysqlDsn`
: a mysql DSN style URL; see [URLs](#urls)

`MariaDsn`
: a mariadb DSN style URL; see [URLs](#urls)

`CockroachDsn`
: a cockroachdb DSN style URL; see [URLs](#urls)

`AmqpDsn`
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

`condate`
: type method for constraining dates;
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