from __future__ import annotations as _annotations

import dataclasses as _dataclasses
import re
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import TYPE_CHECKING, Any

from pydantic_core import MultiHostUrl, PydanticCustomError, Url, core_schema
from typing_extensions import Annotated, TypeAlias

from ._internal import _fields, _repr, _schema_generation_shared
from ._migration import getattr_migration
from .json_schema import JsonSchemaValue

if TYPE_CHECKING:
    import email_validator

    NetworkType: TypeAlias = 'str | bytes | int | tuple[str | bytes | int, str | int]'

else:
    email_validator = None


__all__ = [
    'AnyUrl',
    'AnyHttpUrl',
    'FileUrl',
    'HttpUrl',
    'UrlConstraints',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'CockroachDsn',
    'AmqpDsn',
    'RedisDsn',
    'MongoDsn',
    'KafkaDsn',
    'validate_email',
    'MySQLDsn',
    'MariaDBDsn',
]


@_dataclasses.dataclass
class UrlConstraints(_fields.PydanticMetadata):
    max_length: int | None = None
    allowed_schemes: list[str] | None = None
    host_required: bool | None = None
    default_host: str | None = None
    default_port: int | None = None
    default_path: str | None = None

    def __hash__(self) -> int:
        return hash(
            (
                self.max_length,
                tuple(self.allowed_schemes) if self.allowed_schemes is not None else None,
                self.host_required,
                self.default_host,
                self.default_port,
                self.default_path,
            )
        )


AnyUrl = Url
# host_required is false because all schemes are "special" so host is required by rust-url automatically
AnyHttpUrl = Annotated[Url, UrlConstraints(allowed_schemes=['http', 'https'])]
HttpUrl = Annotated[Url, UrlConstraints(max_length=2083, allowed_schemes=['http', 'https'])]
FileUrl = Annotated[Url, UrlConstraints(allowed_schemes=['file'])]
PostgresDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            'postgres',
            'postgresql',
            'postgresql+asyncpg',
            'postgresql+pg8000',
            'postgresql+psycopg',
            'postgresql+psycopg2',
            'postgresql+psycopg2cffi',
            'postgresql+py-postgresql',
            'postgresql+pygresql',
        ],
    ),
]

CockroachDsn = Annotated[
    Url,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            'cockroachdb',
            'cockroachdb+psycopg2',
            'cockroachdb+asyncpg',
        ],
    ),
]
AmqpDsn = Annotated[Url, UrlConstraints(allowed_schemes=['amqp', 'amqps'])]
RedisDsn = Annotated[
    Url,
    UrlConstraints(allowed_schemes=['redis', 'rediss'], default_host='localhost', default_port=6379, default_path='/0'),
]
MongoDsn = Annotated[MultiHostUrl, UrlConstraints(allowed_schemes=['mongodb', 'mongodb+srv'], default_port=27017)]
KafkaDsn = Annotated[Url, UrlConstraints(allowed_schemes=['kafka'], default_host='localhost', default_port=9092)]
MySQLDsn = Annotated[
    Url,
    UrlConstraints(
        allowed_schemes=[
            'mysql',
            'mysql+mysqlconnector',
            'mysql+aiomysql',
            'mysql+asyncmy',
            'mysql+mysqldb',
            'mysql+pymysql',
            'mysql+cymysql',
            'mysql+pyodbc',
        ],
        default_port=3306,
    ),
]
MariaDBDsn = Annotated[
    Url,
    UrlConstraints(
        allowed_schemes=['mariadb', 'mariadb+mariadbconnector', 'mariadb+pymysql'],
        default_port=3306,
    ),
]


def import_email_validator() -> None:
    global email_validator
    try:
        import email_validator
    except ImportError as e:
        raise ImportError('email-validator is not installed, run `pip install pydantic[email]`') from e


if TYPE_CHECKING:
    EmailStr = Annotated[str, ...]
else:

    class EmailStr:
        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source: type[Any],
        ) -> core_schema.CoreSchema:
            import_email_validator()
            return core_schema.general_after_validator_function(cls.validate, core_schema.str_schema())

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            field_schema = handler(core_schema)
            field_schema.update(type='string', format='email')
            return field_schema

        @classmethod
        def validate(cls, __input_value: str, _: core_schema.ValidationInfo) -> str:
            return validate_email(__input_value)[1]


class NameEmail(_repr.Representation):
    __slots__ = 'name', 'email'

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, NameEmail) and (self.name, self.email) == (other.name, other.email)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.update(type='string', format='name-email')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
    ) -> core_schema.CoreSchema:
        import_email_validator()
        return core_schema.general_after_validator_function(
            cls._validate,
            core_schema.union_schema([core_schema.is_instance_schema(cls), core_schema.str_schema()]),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, __input_value: NameEmail | str, _: core_schema.ValidationInfo) -> NameEmail:
        if isinstance(__input_value, cls):
            return __input_value
        else:
            name, email = validate_email(__input_value)  # type: ignore[arg-type]
            return cls(name, email)

    def __str__(self) -> str:
        return f'{self.name} <{self.email}>'


class IPvAnyAddress:
    __slots__ = ()

    def __new__(cls, value: Any) -> IPv4Address | IPv6Address:  # type: ignore[misc]
        try:
            return IPv4Address(value)
        except ValueError:
            pass

        try:
            return IPv6Address(value)
        except ValueError:
            raise PydanticCustomError('ip_any_address', 'value is not a valid IPv4 or IPv6 address')

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = {}
        field_schema.update(type='string', format='ipvanyaddress')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
    ) -> core_schema.CoreSchema:
        return core_schema.general_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, __input_value: Any, _: core_schema.ValidationInfo) -> IPv4Address | IPv6Address:
        return cls(__input_value)  # type: ignore[return-value]


class IPvAnyInterface:
    __slots__ = ()

    def __new__(cls, value: NetworkType) -> IPv4Interface | IPv6Interface:  # type: ignore[misc]
        try:
            return IPv4Interface(value)
        except ValueError:
            pass

        try:
            return IPv6Interface(value)
        except ValueError:
            raise PydanticCustomError('ip_any_interface', 'value is not a valid IPv4 or IPv6 interface')

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = {}
        field_schema.update(type='string', format='ipvanyinterface')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
    ) -> core_schema.CoreSchema:
        return core_schema.general_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, __input_value: NetworkType, _: core_schema.ValidationInfo) -> IPv4Interface | IPv6Interface:
        return cls(__input_value)  # type: ignore[return-value]


class IPvAnyNetwork:
    __slots__ = ()

    def __new__(cls, value: NetworkType) -> IPv4Network | IPv6Network:  # type: ignore[misc]
        # Assume IP Network is defined with a default value for `strict` argument.
        # Define your own class if you want to specify network address check strictness.
        try:
            return IPv4Network(value)
        except ValueError:
            pass

        try:
            return IPv6Network(value)
        except ValueError:
            raise PydanticCustomError('ip_any_network', 'value is not a valid IPv4 or IPv6 network')

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = {}
        field_schema.update(type='string', format='ipvanynetwork')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
    ) -> core_schema.CoreSchema:
        return core_schema.general_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, __input_value: NetworkType, _: core_schema.ValidationInfo) -> IPv4Network | IPv6Network:
        return cls(__input_value)  # type: ignore[return-value]


pretty_email_regex = re.compile(r' *([\w ]*?) *<(.+?)> *')


def validate_email(value: str) -> tuple[str, str]:
    """
    Email address validation using https://pypi.org/project/email-validator/

    Notes:
    * raw ip address (literal) domain parts are not allowed.
    * "John Doe <local_part@domain.com>" style "pretty" email addresses are processed
    * spaces are striped from the beginning and end of addresses but no error is raised
    """
    if email_validator is None:
        import_email_validator()

    m = pretty_email_regex.fullmatch(value)
    name: str | None = None
    if m:
        name, value = m.groups()

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


__getattr__ = getattr_migration(__name__)
