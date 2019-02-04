import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional, Pattern, Set, Type, Union
from uuid import UUID

from . import errors
from .utils import import_string, make_dsn, url_regex_generator, validate_email
from .validators import (
    anystr_length_validator,
    anystr_strip_whitespace,
    bytes_validator,
    decimal_validator,
    float_validator,
    int_validator,
    not_none_validator,
    number_multiple_validator,
    number_size_validator,
    path_exists_validator,
    path_validator,
    str_validator,
)

try:
    import email_validator
except ImportError:
    email_validator = None

__all__ = [
    'NoneStr',
    'NoneBytes',
    'StrBytes',
    'NoneStrBytes',
    'StrictStr',
    'ConstrainedBytes',
    'conbytes',
    'ConstrainedStr',
    'constr',
    'EmailStr',
    'UrlStr',
    'urlstr',
    'NameEmail',
    'PyObject',
    'DSN',
    'ConstrainedInt',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'ConstrainedFloat',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'ConstrainedDecimal',
    'condecimal',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'FilePath',
    'DirectoryPath',
    'Json',
    'JsonWrapper',
]

NoneStr = Optional[str]
NoneBytes = Optional[bytes]
StrBytes = Union[str, bytes]
NoneStrBytes = Optional[StrBytes]


class StrictStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise errors.StrError()
        return v


class ConstrainedBytes(bytes):
    strip_whitespace = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    @classmethod
    def __get_validators__(cls):
        yield not_none_validator
        yield bytes_validator
        yield anystr_strip_whitespace
        yield anystr_length_validator


def conbytes(*, strip_whitespace=False, min_length=None, max_length=None) -> Type[bytes]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(strip_whitespace=strip_whitespace, min_length=min_length, max_length=max_length)
    return type('ConstrainedBytesValue', (ConstrainedBytes,), namespace)


class ConstrainedStr(str):
    strip_whitespace = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    curtail_length: Optional[int] = None
    regex: Optional[Pattern] = None

    @classmethod
    def __get_validators__(cls):
        yield not_none_validator
        yield str_validator
        yield anystr_strip_whitespace
        yield anystr_length_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if cls.curtail_length and len(value) > cls.curtail_length:
            value = value[: cls.curtail_length]

        if cls.regex:
            if not cls.regex.match(value):
                raise errors.StrRegexError(pattern=cls.regex.pattern)

        return value


def constr(*, strip_whitespace=False, min_length=None, max_length=None, curtail_length=None, regex=None) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
        regex=regex and re.compile(regex),
    )
    return type('ConstrainedStrValue', (ConstrainedStr,), namespace)


class EmailStr(str):
    @classmethod
    def __get_validators__(cls):
        # included here and below so the error happens straight away
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return validate_email(value)[1]


class UrlStr(str):
    strip_whitespace = True
    min_length = 1
    max_length = 2 ** 16
    schemes: Optional[Set[str]] = None
    relative = False  # whether to allow relative URLs
    require_tld = True  # whether to reject non-FQDN hostnames

    @classmethod
    def __get_validators__(cls):
        yield not_none_validator
        yield str_validator
        yield anystr_strip_whitespace
        yield anystr_length_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        # Check first if the scheme is valid
        schemes = cls.schemes or {'http', 'https', 'ftp', 'ftps'}
        if '://' in value:
            scheme = value.split('://')[0].lower()
            if scheme not in schemes:
                raise errors.UrlSchemeError(scheme=scheme)

        regex = url_regex_generator(relative=cls.relative, require_tld=cls.require_tld)
        if not regex.match(value):
            raise errors.UrlRegexError()

        return value


def urlstr(
    *,
    strip_whitespace=True,
    min_length=1,
    max_length=2 ** 16,
    relative=False,
    require_tld=True,
    schemes: Optional[Set[str]] = None,
) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        relative=relative,
        require_tld=require_tld,
        schemes=schemes,
    )
    return type('UrlStrValue', (UrlStr,), namespace)


class NameEmail:
    __slots__ = 'name', 'email'

    def __init__(self, name, email):
        self.name = name
        self.email = email

    @classmethod
    def __get_validators__(cls):
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return cls(*validate_email(value))

    def __str__(self):
        return f'{self.name} <{self.email}>'

    def __repr__(self):
        return f'<NameEmail("{self}")>'


class PyObject:
    validate_always = True

    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if value is not None:
            try:
                return import_string(value)
            except ImportError as e:
                raise errors.PyObjectError(error_message=str(e))


class DSN(str):
    prefix = 'db_'
    fields = 'driver', 'user', 'password', 'host', 'port', 'name', 'query'
    validate_always = True

    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value, values, **kwarg):
        if value:
            return value

        kwargs = {f: values.get(cls.prefix + f) for f in cls.fields}
        if kwargs['driver'] is None:
            raise errors.DSNDriverIsEmptyError()

        return make_dsn(**kwargs)


class ConstrainedNumberMeta(type):
    def __new__(cls, name, bases, dct):
        new_cls = type.__new__(cls, name, bases, dct)

        if new_cls.gt is not None and new_cls.ge is not None:
            raise errors.ConfigError('bounds gt and ge cannot be specified at the same time')
        if new_cls.lt is not None and new_cls.le is not None:
            raise errors.ConfigError('bounds lt and le cannot be specified at the same time')

        return new_cls


class ConstrainedInt(int, metaclass=ConstrainedNumberMeta):
    gt: Optional[int] = None
    ge: Optional[int] = None
    lt: Optional[int] = None
    le: Optional[int] = None
    multiple_of: Optional[Union[int, float]] = None

    @classmethod
    def __get_validators__(cls):
        yield int_validator
        yield number_size_validator
        yield number_multiple_validator


def conint(*, gt=None, ge=None, lt=None, le=None, multiple_of=None) -> Type[int]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return type('ConstrainedIntValue', (ConstrainedInt,), namespace)


class PositiveInt(ConstrainedInt):
    gt = 0


class NegativeInt(ConstrainedInt):
    lt = 0


class ConstrainedFloat(float, metaclass=ConstrainedNumberMeta):
    gt: Union[None, int, float] = None
    ge: Union[None, int, float] = None
    lt: Union[None, int, float] = None
    le: Union[None, int, float] = None
    multiple_of: Optional[Union[int, float]] = None

    @classmethod
    def __get_validators__(cls):
        yield float_validator
        yield number_size_validator
        yield number_multiple_validator


def confloat(*, gt=None, ge=None, lt=None, le=None, multiple_of=None) -> Type[float]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return type('ConstrainedFloatValue', (ConstrainedFloat,), namespace)


class PositiveFloat(ConstrainedFloat):
    gt = 0


class NegativeFloat(ConstrainedFloat):
    lt = 0


class ConstrainedDecimal(Decimal, metaclass=ConstrainedNumberMeta):
    gt: Union[None, int, float, Decimal] = None
    ge: Union[None, int, float, Decimal] = None
    lt: Union[None, int, float, Decimal] = None
    le: Union[None, int, float, Decimal] = None
    max_digits: Optional[int] = None
    decimal_places: Optional[int] = None
    multiple_of: Optional[Union[int, float]] = None

    @classmethod
    def __get_validators__(cls):
        yield not_none_validator
        yield decimal_validator
        yield number_size_validator
        yield number_multiple_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Decimal) -> Decimal:
        digit_tuple, exponent = value.as_tuple()[1:]
        if exponent in {'F', 'n', 'N'}:
            raise errors.DecimalIsNotFiniteError()

        if exponent >= 0:
            # A positive exponent adds that many trailing zeros.
            digits = len(digit_tuple) + exponent
            decimals = 0
        else:
            # If the absolute value of the negative exponent is larger than the
            # number of digits, then it's the same as the number of digits,
            # because it'll consume all of the digits in digit_tuple and then
            # add abs(exponent) - len(digit_tuple) leading zeros after the
            # decimal point.
            if abs(exponent) > len(digit_tuple):
                digits = decimals = abs(exponent)
            else:
                digits = len(digit_tuple)
                decimals = abs(exponent)
        whole_digits = digits - decimals

        if cls.max_digits is not None and digits > cls.max_digits:
            raise errors.DecimalMaxDigitsError(max_digits=cls.max_digits)

        if cls.decimal_places is not None and decimals > cls.decimal_places:
            raise errors.DecimalMaxPlacesError(decimal_places=cls.decimal_places)

        if cls.max_digits is not None and cls.decimal_places is not None:
            expected = cls.max_digits - cls.decimal_places
            if whole_digits > expected:
                raise errors.DecimalWholeDigitsError(whole_digits=expected)

        return value


def condecimal(
    *, gt=None, ge=None, lt=None, le=None, max_digits=None, decimal_places=None, multiple_of=None
) -> Type[Decimal]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        gt=gt, ge=ge, lt=lt, le=le, max_digits=max_digits, decimal_places=decimal_places, multiple_of=multiple_of
    )
    return type('ConstrainedDecimalValue', (ConstrainedDecimal,), namespace)


class UUID1(UUID):
    _required_version = 1


class UUID3(UUID):
    _required_version = 3


class UUID4(UUID):
    _required_version = 4


class UUID5(UUID):
    _required_version = 5


class FilePath(Path):
    @classmethod
    def __get_validators__(cls):
        yield path_validator
        yield path_exists_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Path) -> Path:
        if not value.is_file():
            raise errors.PathNotAFileError(path=value)

        return value


class DirectoryPath(Path):
    @classmethod
    def __get_validators__(cls):
        yield path_validator
        yield path_exists_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Path) -> Path:
        if not value.is_dir():
            raise errors.PathNotADirectoryError(path=value)

        return value


class JsonWrapper:
    __slots__ = ('inner_type',)


class JsonMeta(type):
    def __getitem__(self, t):
        return type('JsonWrapperValue', (JsonWrapper,), {'inner_type': t})


class Json(metaclass=JsonMeta):
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, v: str):
        try:
            return json.loads(v)
        except ValueError:
            raise errors.JsonError()
        except TypeError:
            raise errors.JsonTypeError()
