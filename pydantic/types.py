import json
import re
from colorsys import rgb_to_hls
from decimal import Decimal
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
    _BaseAddress,
    _BaseNetwork,
)
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, Optional, Pattern, Set, Tuple, Type, Union, cast
from uuid import UUID

from . import colors, errors
from .utils import AnyType, change_exception, import_string, make_dsn, url_regex_generator, validate_email
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
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'SecretStr',
    'SecretBytes',
    'Color',
]

NoneStr = Optional[str]
NoneBytes = Optional[bytes]
StrBytes = Union[str, bytes]
NoneStrBytes = Optional[StrBytes]
OptionalInt = Optional[int]
OptionalIntFloat = Union[OptionalInt, float]
OptionalIntFloatDecimal = Union[OptionalIntFloat, Decimal]
NetworkType = Union[str, bytes, int, Tuple[Union[str, bytes, int], Union[str, int]]]
RGBType = Tuple[int, int, int]
RGBAType = Tuple[int, int, int, float]
AnyRGBType = Union[RGBType, RGBAType]
RGBFractionType = Tuple[float, float, float]
HLSType = Tuple[float, float, float]
ColorType = Union[str, AnyRGBType]


if TYPE_CHECKING:  # pragma: no cover
    from .dataclasses import DataclassType  # noqa: F401
    from .main import BaseModel  # noqa: F401
    from .utils import AnyCallable

    CallableGenerator = Generator[AnyCallable, None, None]
    ModelOrDc = Type[Union['BaseModel', 'DataclassType']]


class StrictStr(str):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise errors.StrError()
        return v


class ConstrainedBytes(bytes):
    strip_whitespace = False
    min_length: OptionalInt = None
    max_length: OptionalInt = None

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield not_none_validator
        yield bytes_validator
        yield anystr_strip_whitespace
        yield anystr_length_validator


def conbytes(*, strip_whitespace: bool = False, min_length: int = None, max_length: int = None) -> Type[bytes]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(strip_whitespace=strip_whitespace, min_length=min_length, max_length=max_length)
    return type('ConstrainedBytesValue', (ConstrainedBytes,), namespace)


class ConstrainedStr(str):
    strip_whitespace = False
    min_length: OptionalInt = None
    max_length: OptionalInt = None
    curtail_length: OptionalInt = None
    regex: Optional[Pattern[str]] = None

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
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


def constr(
    *,
    strip_whitespace: bool = False,
    min_length: int = None,
    max_length: int = None,
    curtail_length: int = None,
    regex: str = None,
) -> Type[str]:
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
    def __get_validators__(cls) -> 'CallableGenerator':
        # included here and below so the error happens straight away
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        return validate_email(value)[1]


class UrlStr(str):
    strip_whitespace = True
    min_length = 1
    max_length = 2 ** 16
    schemes: Optional[Set[str]] = None
    relative = False  # whether to allow relative URLs
    require_tld = True  # whether to reject non-FQDN hostnames

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
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
    strip_whitespace: bool = True,
    min_length: int = 1,
    max_length: int = 2 ** 16,
    relative: bool = False,
    require_tld: bool = True,
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

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> 'NameEmail':
        return cls(*validate_email(value))

    def __str__(self) -> str:
        return f'{self.name} <{self.email}>'

    def __repr__(self) -> str:
        return f'<NameEmail("{self}")>'


class PyObject:
    validate_always = True

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Any:
        if isinstance(value, Callable):  # type: ignore
            return value

        try:
            value = str_validator(value)
        except errors.StrError:
            raise errors.PyObjectError(error_message='value is neither a valid import path not a valid callable')

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
    def __get_validators__(cls) -> 'CallableGenerator':
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str, values: Dict[str, Any]) -> str:
        if value:
            return value

        kwargs = {f: values.get(cls.prefix + f) for f in cls.fields}
        if kwargs['driver'] is None:
            raise errors.DSNDriverIsEmptyError()

        return make_dsn(**kwargs)  # type: ignore


class ConstrainedNumberMeta(type):
    def __new__(cls, name: str, bases: Any, dct: Dict[str, Any]) -> 'ConstrainedInt':
        new_cls = cast('ConstrainedInt', type.__new__(cls, name, bases, dct))

        if new_cls.gt is not None and new_cls.ge is not None:
            raise errors.ConfigError('bounds gt and ge cannot be specified at the same time')
        if new_cls.lt is not None and new_cls.le is not None:
            raise errors.ConfigError('bounds lt and le cannot be specified at the same time')

        return new_cls


class ConstrainedInt(int, metaclass=ConstrainedNumberMeta):
    gt: OptionalInt = None
    ge: OptionalInt = None
    lt: OptionalInt = None
    le: OptionalInt = None
    multiple_of: OptionalInt = None

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield int_validator
        yield number_size_validator
        yield number_multiple_validator


def conint(*, gt: int = None, ge: int = None, lt: int = None, le: int = None, multiple_of: int = None) -> Type[int]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return type('ConstrainedIntValue', (ConstrainedInt,), namespace)


class PositiveInt(ConstrainedInt):
    gt = 0


class NegativeInt(ConstrainedInt):
    lt = 0


class ConstrainedFloat(float, metaclass=ConstrainedNumberMeta):
    gt: OptionalIntFloat = None
    ge: OptionalIntFloat = None
    lt: OptionalIntFloat = None
    le: OptionalIntFloat = None
    multiple_of: OptionalIntFloat = None

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield float_validator
        yield number_size_validator
        yield number_multiple_validator


def confloat(
    *, gt: float = None, ge: float = None, lt: float = None, le: float = None, multiple_of: float = None
) -> Type[float]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return type('ConstrainedFloatValue', (ConstrainedFloat,), namespace)


class PositiveFloat(ConstrainedFloat):
    gt = 0


class NegativeFloat(ConstrainedFloat):
    lt = 0


class ConstrainedDecimal(Decimal, metaclass=ConstrainedNumberMeta):
    gt: OptionalIntFloatDecimal = None
    ge: OptionalIntFloatDecimal = None
    lt: OptionalIntFloatDecimal = None
    le: OptionalIntFloatDecimal = None
    max_digits: OptionalInt = None
    decimal_places: OptionalInt = None
    multiple_of: OptionalIntFloatDecimal = None

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
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
    *,
    gt: Decimal = None,
    ge: Decimal = None,
    lt: Decimal = None,
    le: Decimal = None,
    max_digits: int = None,
    decimal_places: int = None,
    multiple_of: Decimal = None,
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
    def __get_validators__(cls) -> 'CallableGenerator':
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
    def __get_validators__(cls) -> 'CallableGenerator':
        yield path_validator
        yield path_exists_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Path) -> Path:
        if not value.is_dir():
            raise errors.PathNotADirectoryError(path=value)

        return value


class JsonWrapper:
    pass


class JsonMeta(type):
    def __getitem__(self, t: AnyType) -> Type[JsonWrapper]:
        return type('JsonWrapperValue', (JsonWrapper,), {'inner_type': t})


class Json(metaclass=JsonMeta):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> Any:
        try:
            return json.loads(v)
        except ValueError:
            raise errors.JsonError()
        except TypeError:
            raise errors.JsonTypeError()


class IPvAnyAddress(_BaseAddress):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, bytes, int]) -> Union[IPv4Address, IPv6Address]:
        try:
            return IPv4Address(value)
        except ValueError:
            pass

        with change_exception(errors.IPvAnyAddressError, ValueError):
            return IPv6Address(value)


class IPvAnyInterface(_BaseAddress):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: NetworkType) -> Union[IPv4Interface, IPv6Interface]:
        try:
            return IPv4Interface(value)
        except ValueError:
            pass

        with change_exception(errors.IPvAnyInterfaceError, ValueError):
            return IPv6Interface(value)


class IPvAnyNetwork(_BaseNetwork):  # type: ignore
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: NetworkType) -> Union[IPv4Network, IPv6Network]:
        # Assume IP Network is defined with a default value for ``strict`` argument.
        # Define your own class if you want to specify network address check strictness.
        try:
            return IPv4Network(value)
        except ValueError:
            pass

        with change_exception(errors.IPvAnyNetworkError, ValueError):
            return IPv6Network(value)


class SecretStr:
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> 'SecretStr':
        return cls(value)

    def __init__(self, value: str):
        self._secret_value = value

    def __repr__(self) -> str:
        return "SecretStr('**********')" if self._secret_value else "SecretStr('')"

    def __str__(self) -> str:
        return repr(self)

    def display(self) -> str:
        return '**********' if self._secret_value else ''

    def get_secret_value(self) -> str:
        return self._secret_value


class SecretBytes:
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield bytes_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: bytes) -> 'SecretBytes':
        return cls(value)

    def __init__(self, value: bytes):
        self._secret_value = value

    def __repr__(self) -> str:
        return "SecretBytes(b'**********')" if self._secret_value else "SecretBytes(b'')"

    def __str__(self) -> str:
        return repr(self)

    def display(self) -> str:
        return '**********' if self._secret_value else ''

    def get_secret_value(self) -> bytes:
        return self._secret_value


class Color:
    __slots__ = '_original', '_color_match'

    def __init__(self, value: ColorType) -> None:
        self._original: ColorType = value
        self._color_match: Optional[str] = None
        self._parse_color()

    @staticmethod
    def _rgb_str_to_tuple(value: str) -> Optional[RGBAType]:
        """
        Return RGB/RGBA tuple from the passed string.

        If RGBA cannot be matched, return None
        """
        r = re.compile(
            r'rgba?\((?P<red>\d{1,3}),\s*'
            r'(?P<green>\d{1,3}),\s*'
            r'(?P<blue>\d{1,3})'
            r'(,\s*(?P<alpha>\d{1}\.\d{1,}))?\)',
            re.IGNORECASE,
        )
        match = r.match(value)

        if match is None:
            return None

        red = int(match.group('red'))
        green = int(match.group('green'))
        blue = int(match.group('blue'))
        alpha = float(match.group('alpha')) if match.group('alpha') is not None else 1.0
        return red, green, blue, alpha

    @staticmethod
    def _almost_equal(value_1: float, value_2: float = 1.0) -> bool:
        """
        Return True if two floats are almost equal
        """
        return abs(value_1 - value_2) <= 1e-8

    @staticmethod
    def _tuple_to_rgb(value: Optional[Tuple[Any, ...]]) -> Optional[RGBType]:
        """
        Convert a tuple to RGB tuple, if it fails raise an error
        """

        def is_int_color(c: Any) -> bool:
            try:
                color = int(c)
            except ValueError:
                return False
            return color in range(0, 256)

        result = None
        if value is None:
            return result

        length = len(value)
        if length not in range(3, 5):
            return result

        if length == 4:
            try:
                Color._almost_equal(float(value[3]), 1.0)
            except ValueError:
                return result

        if any(map(lambda color: not is_int_color(color), value)):
            return result

        r, g, b = value[:3]
        return r, g, b

    def _parse_tuple(self, value: Optional[Tuple[Any, ...]]) -> Optional[str]:
        """
        Get name of the color by its RGB
        """
        rgb = self._tuple_to_rgb(value)
        name = colors.BY_RGB.get(rgb, None)  # type: ignore
        return name

    def _parse_rgb_str(self, value: str) -> Optional[str]:
        """
        Get name of the color by its RGB/RGBA string
        """
        rgba = self._rgb_str_to_tuple(value)
        return self._parse_tuple(rgba)

    def _parse_hex_str(self, value: str) -> Optional[str]:
        """
        Get name of the color by its hexadecimal string
        """
        if value.startswith('#'):
            pure_hex = value[1:]
        elif value.startswith('0x'):
            pure_hex = value[2:]
        else:
            pure_hex = value

        if len(pure_hex) == 3:
            pure_hex = colors.expand_3_digit_hex(pure_hex)

        return colors.BY_HEX.get(pure_hex)

    def _parse_color(self) -> None:
        """
        Main logic of color parsing
        """
        if isinstance(self._original, tuple):
            self._color_match = self._parse_tuple(self._original)

        elif isinstance(self._original, str):
            color = self._original.lower()

            # rgb/rgba string
            self._color_match = self._parse_rgb_str(color)
            if self._color_match is not None:
                return

            # hex string
            self._color_match = self._parse_hex_str(color)
            if self._color_match is not None:
                return

            # named colour
            if color in colors.BY_NAME:
                self._color_match = color
                return

    def _get_color_or_raise(self) -> None:
        """
        Raise error if color name not found
        """
        if self._color_match is None:
            raise errors.ColorError()

    def original(self) -> ColorType:
        """
        Return original value passed to the model
        """
        return self._original

    def as_hex(self, prefix: str = '0x', reduce: bool = True) -> str:
        """
        Return hexadecimal value of the color

        Try reduce hex code to 3-digit format, fallback to 6-digit.
        """
        self._get_color_or_raise()
        hexadecimal, _ = colors.BY_NAME[self._color_match or '']
        return '{}{}'.format(prefix, colors.reduce_6_digit_hex(hexadecimal) if reduce else hexadecimal)

    def as_tuple(self, alpha: bool = False) -> AnyRGBType:
        """
        Return RGB or RGBA tuple
        """
        self._get_color_or_raise()
        _, rgb = colors.BY_NAME[self._color_match or '']
        r, g, b = rgb

        if alpha:
            return r, g, b, 1.0
        return r, g, b

    def as_rgb(self, alpha: bool = False) -> str:
        """
        Return RGB or RGBA string representation of the color
        """
        rgb = self.as_tuple(alpha)
        if alpha:
            return 'rgba({}, {}, {}, {})'.format(*rgb)
        return 'rgb({}, {}, {})'.format(*rgb)

    def as_named_color(self) -> str:
        """
        Return name of the color as per CSS3 specification.
        """
        self._get_color_or_raise()
        return self._color_match  # type: ignore

    def as_hls(self) -> HLSType:
        """
        Return tuple of floats representing Hue Lightness Saturation (HLS) color
        """

        def normalize(v: Union[int, float, str]) -> float:
            return float(v) / 255

        self._get_color_or_raise()
        r, g, b = self.as_tuple(alpha=False)  # type: ignore
        return rgb_to_hls(normalize(r), normalize(g), normalize(b))

    def __str__(self) -> str:
        return str(self._original).lower()

    def __repr__(self) -> str:
        return '<Color("{}")>'.format(self._color_match or self._original)

    @staticmethod
    def dumps(value: 'Color') -> str:
        """
        Encoder for json.dumps
        """
        return value.as_named_color()

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: ColorType) -> 'Color':
        color = cls(value)
        color._get_color_or_raise()
        return color
