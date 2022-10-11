import abc
import dataclasses as _dataclasses
import re
import warnings
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Dict,
    FrozenSet,
    Hashable,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

import annotated_types
from pydantic_core import PydanticCustomError, core_schema

from . import errors
from ._internal import _fields, _validators

__all__ = [
    'StrictStr',
    'conbytes',
    'conlist',
    'conset',
    'confrozenset',
    'constr',
    'ImportString',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'NonNegativeInt',
    'NonPositiveInt',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'NonNegativeFloat',
    'NonPositiveFloat',
    'FiniteFloat',
    'condecimal',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'FilePath',
    'DirectoryPath',
    'Json',
    'JsonWrapper',
    'SecretField',
    'SecretStr',
    'SecretBytes',
    'StrictBool',
    'StrictBytes',
    'StrictInt',
    'StrictFloat',
    'PaymentCardNumber',
    'ByteSize',
    'PastDate',
    'FutureDate',
    'ConstrainedDate',
    'condate',
]

if TYPE_CHECKING:
    from ._internal._typing_extra import CallableGenerator
    from .dataclasses import Dataclass
    from .main import BaseModel

    ModelOrDc = Type[Union[BaseModel, Dataclass]]


@_dataclasses.dataclass
class Strict(_fields.PydanticMetadata):
    strict: bool | None = True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BOOLEAN TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

StrictBool = Annotated[bool, Strict()]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INTEGER TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def conint(
    *, strict: bool = None, gt: int = None, ge: int = None, lt: int = None, le: int = None, multiple_of: int = None
) -> type[int]:
    return Annotated[
        int,
        Strict(strict),
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of),
    ]


PositiveInt = Annotated[int, annotated_types.Gt(0)]
NegativeInt = Annotated[int, annotated_types.Lt(0)]
NonPositiveInt = Annotated[int, annotated_types.Le(0)]
NonNegativeInt = Annotated[int, annotated_types.Ge(0)]
StrictInt = Annotated[int, Strict()]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FLOAT TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class AllowInfNan(_fields.PydanticMetadata):
    allow_inf_nan: bool | None = True


def confloat(
    *,
    strict: bool = False,
    gt: float = None,
    ge: float = None,
    lt: float = None,
    le: float = None,
    multiple_of: float = None,
    allow_inf_nan: Optional[bool] = None,
) -> type[float]:
    return Annotated[
        float,
        Strict(strict),
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of),
        AllowInfNan(allow_inf_nan),
    ]


PositiveFloat = Annotated[float, annotated_types.Gt(0)]
NegativeFloat = Annotated[float, annotated_types.Lt(0)]
NonPositiveFloat = Annotated[float, annotated_types.Le(0)]
NonNegativeFloat = Annotated[float, annotated_types.Ge(0)]
StrictFloat = Annotated[float, Strict(True)]
FiniteFloat = Annotated[float, AllowInfNan(False)]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BYTES TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def conbytes(
    *,
    min_length: int = None,
    max_length: int = None,
    strict: bool = None,
) -> type[bytes]:
    return Annotated[bytes, Strict(strict), annotated_types.Len(min_length, max_length)]


StrictBytes = Annotated[bytes, Strict()]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STRING TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def constr(
    *,
    strip_whitespace: bool = False,
    to_upper: bool = False,
    to_lower: bool = False,
    strict: bool = False,
    min_length: int = None,
    max_length: int = None,
    pattern: str = None,
) -> type[str]:
    return Annotated[
        str,
        Strict(strict),
        annotated_types.Len(min_length, max_length),
        _fields.CustomMetadata(
            strip_whitespace=strip_whitespace,
            to_upper=to_upper,
            to_lower=to_lower,
            pattern=pattern,
        ),
    ]


StrictStr = Annotated[str, Strict()]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ COLLECTION TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
HashableItemType = TypeVar('HashableItemType', bound=Hashable)


def conset(
    item_type: Type[HashableItemType], *, min_length: int = None, max_length: int = None
) -> Type[Set[HashableItemType]]:
    return Annotated[Set[item_type], annotated_types.Len(min_length, max_length)]


def confrozenset(
    item_type: Type[HashableItemType], *, min_length: int = None, max_length: int = None
) -> Type[FrozenSet[HashableItemType]]:
    return Annotated[FrozenSet[item_type], annotated_types.Len(min_length, max_length)]


AnyItemType = TypeVar('AnyItemType')


def conlist(item_type: Type[AnyItemType], *, min_length: int = None, max_length: int = None) -> Type[List[AnyItemType]]:
    return Annotated[List[item_type], annotated_types.Len(min_length, max_length)]


def contuple(
    item_type: Type[AnyItemType], *, min_length: int = None, max_length: int = None
) -> Type[Tuple[AnyItemType]]:
    return Annotated[Tuple[item_type], annotated_types.Len(min_length, max_length)]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ IMPORT STRING TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AnyType = TypeVar('AnyType')
if TYPE_CHECKING:
    ImportString = Annotated[AnyType, ...]
else:

    class ImportString(_fields.PydanticMetadata):
        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_validation_schema__(
            cls, schema: core_schema.CoreSchema | None = None
        ) -> core_schema.CoreSchema:
            if schema is None or schema == {'type': 'any'}:
                # Treat bare usage of ImportString (`schema is None`) as the same as ImportString[Any]
                return core_schema.FunctionPlainSchema(
                    type='function',
                    mode='plain',
                    function=_validators.import_string,
                )
            else:
                return core_schema.FunctionSchema(
                    type='function',
                    mode='before',
                    function=_validators.import_string,
                    schema=schema,
                )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DECIMAL TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def condecimal(
    *,
    strict: bool = None,
    gt: int | Decimal = None,
    ge: int | Decimal = None,
    lt: int | Decimal = None,
    le: int | Decimal = None,
    multiple_of: int | Decimal = None,
    max_digits: int = None,
    decimal_places: int = None,
    allow_inf_nan: Optional[bool] = None,
) -> Type[Decimal]:
    return Annotated[
        Decimal,
        Strict(strict),
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of),
        _fields.CustomMetadata(max_digits=max_digits, decimal_places=decimal_places),
        AllowInfNan(allow_inf_nan),
    ]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UUID TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class UuidVersion(_fields.PydanticMetadata):
    uuid_version: Literal[1, 3, 4, 5]

    def __modify_schema__(self, field_schema: dict[str, Any]) -> None:
        field_schema.update(type='string', format=f'uuid{self.uuid_version}')

    def __get_pydantic_validation_schema__(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        return core_schema.function_after_schema(self.validate, schema)

    def validate(self, value: UUID, **kwargs) -> UUID:
        if value.version != self.uuid_version:
            raise PydanticCustomError(
                'uuid_version', 'uuid version {required_version} expected', {'required_version': self.uuid_version}
            )
        return value


UUID1 = Annotated[UUID, UuidVersion(1)]
UUID3 = Annotated[UUID, UuidVersion(3)]
UUID4 = Annotated[UUID, UuidVersion(4)]
UUID5 = Annotated[UUID, UuidVersion(5)]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PATH TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class PathType(_fields.PydanticMetadata):
    path_type: Literal['file', 'dir', 'new']

    def __modify_schema__(self, field_schema: dict[str, Any]) -> None:
        field_schema.update(format='file-path')

    def __get_pydantic_validation_schema__(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        function_lookup = {
            'file': self.validate_file,
            'dir': self.validate_directory,
            'new': self.validate_new,
        }

        return core_schema.FunctionSchema(
            type='function',
            mode='after',
            function=function_lookup[self.path_type],
            schema=schema,
        )

    @staticmethod
    def validate_file(path: Path) -> Path:
        if path.is_file():
            return path
        else:
            raise PydanticCustomError('path_not_file', 'path does not point to a file')

    @staticmethod
    def validate_directory(path: Path) -> Path:
        if path.is_dir():
            return path
        else:
            raise PydanticCustomError('path_not_directory', 'path does not point to a directory')

    @staticmethod
    def validate_new(path: Path) -> Path:
        if path.exists():
            raise PydanticCustomError('path_exists', 'path already exists')
        elif not path.parent.exists():
            raise PydanticCustomError('parent_does_not_exist', 'parent directory does not exist')
        else:
            return path


FilePath = Annotated[Path, PathType('file')]
DirectoryPath = Annotated[Path, PathType('dir')]
NewPath = Annotated[Path, PathType('new')]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ JSON TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class JsonWrapper:
    pass


class JsonMeta(type):
    def __getitem__(self, t: Type[Any]) -> Type[JsonWrapper]:
        if t is Any:
            return Json  # allow Json[Any] to replecate plain Json
        return type('JsonWrapperValue', (JsonWrapper,), {'inner_type': t})


if TYPE_CHECKING:
    Json = Annotated[ItemType, ...]  # Json[list[str]] will be recognized by type checkers as list[str]

else:

    class Json(metaclass=JsonMeta):
        @classmethod
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(type='string', format='json-string')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SECRET TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class SecretField(abc.ABC):
    """
    Note: this should be implemented as a generic like `SecretField(ABC, Generic[T])`,
          the `__init__()` should be part of the abstract class and the
          `get_secret_value()` method should use the generic `T` type.

          However Cython doesn't support very well generics at the moment and
          the generated code fails to be imported (see
          https://github.com/cython/cython/issues/2753).
    """

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.get_secret_value() == other.get_secret_value()

    def __str__(self) -> str:
        return '**********' if self.get_secret_value() else ''

    def __hash__(self) -> int:
        return hash(self.get_secret_value())

    @abc.abstractmethod
    def get_secret_value(self) -> Any:  # pragma: no cover
        ...


class SecretStr(SecretField):
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            type='string',
            writeOnly=True,
            format='password',
            minLength=cls.min_length,
            maxLength=cls.max_length,
        )

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate
        yield constr_length_validator

    @classmethod
    def validate(cls, value: Any) -> 'SecretStr':
        if isinstance(value, cls):
            return value
        value = str_validator(value)
        return cls(value)

    def __init__(self, value: str):
        self._secret_value = value

    def __repr__(self) -> str:
        return f"SecretStr('{self}')"

    def __len__(self) -> int:
        return len(self._secret_value)

    def display(self) -> str:
        warnings.warn('`secret_str.display()` is deprecated, use `str(secret_str)` instead', DeprecationWarning)
        return str(self)

    def get_secret_value(self) -> str:
        return self._secret_value


class SecretBytes(SecretField):
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            type='string',
            writeOnly=True,
            format='password',
            minLength=cls.min_length,
            maxLength=cls.max_length,
        )

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate
        yield constr_length_validator

    @classmethod
    def validate(cls, value: Any) -> 'SecretBytes':
        if isinstance(value, cls):
            return value
        value = bytes_validator(value)
        return cls(value)

    def __init__(self, value: bytes):
        self._secret_value = value

    def __repr__(self) -> str:
        return f"SecretBytes(b'{self}')"

    def __len__(self) -> int:
        return len(self._secret_value)

    def display(self) -> str:
        warnings.warn('`secret_bytes.display()` is deprecated, use `str(secret_bytes)` instead', DeprecationWarning)
        return str(self)

    def get_secret_value(self) -> bytes:
        return self._secret_value


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PAYMENT CARD TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PaymentCardBrand(str, Enum):
    # If you add another card type, please also add it to the
    # Hypothesis strategy in `pydantic._hypothesis_plugin`.
    amex = 'American Express'
    mastercard = 'Mastercard'
    visa = 'Visa'
    other = 'other'

    def __str__(self) -> str:
        return self.value


class PaymentCardNumber(str):
    """
    Based on: https://en.wikipedia.org/wiki/Payment_card_number
    """

    strip_whitespace: ClassVar[bool] = True
    min_length: ClassVar[int] = 12
    max_length: ClassVar[int] = 19
    bin: str
    last4: str
    brand: PaymentCardBrand

    def __init__(self, card_number: str):
        self.bin = card_number[:6]
        self.last4 = card_number[-4:]
        self.brand = self._get_brand(card_number)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield str_validator
        yield constr_strip_whitespace
        yield constr_length_validator
        yield cls.validate_digits
        yield cls.validate_luhn_check_digit
        yield cls
        yield cls.validate_length_for_brand

    @property
    def masked(self) -> str:
        num_masked = len(self) - 10  # len(bin) + len(last4) == 10
        return f'{self.bin}{"*" * num_masked}{self.last4}'

    @classmethod
    def validate_digits(cls, card_number: str) -> str:
        if not card_number.isdigit():
            raise errors.NotDigitError
        return card_number

    @classmethod
    def validate_luhn_check_digit(cls, card_number: str) -> str:
        """
        Based on: https://en.wikipedia.org/wiki/Luhn_algorithm
        """
        sum_ = int(card_number[-1])
        length = len(card_number)
        parity = length % 2
        for i in range(length - 1):
            digit = int(card_number[i])
            if i % 2 == parity:
                digit *= 2
            if digit > 9:
                digit -= 9
            sum_ += digit
        valid = sum_ % 10 == 0
        if not valid:
            raise errors.LuhnValidationError
        return card_number

    @classmethod
    def validate_length_for_brand(cls, card_number: 'PaymentCardNumber') -> 'PaymentCardNumber':
        """
        Validate length based on BIN for major brands:
        https://en.wikipedia.org/wiki/Payment_card_number#Issuer_identification_number_(IIN)
        """
        required_length: Union[None, int, str] = None
        if card_number.brand in PaymentCardBrand.mastercard:
            required_length = 16
            valid = len(card_number) == required_length
        elif card_number.brand == PaymentCardBrand.visa:
            required_length = '13, 16 or 19'
            valid = len(card_number) in {13, 16, 19}
        elif card_number.brand == PaymentCardBrand.amex:
            required_length = 15
            valid = len(card_number) == required_length
        else:
            valid = True
        if not valid:
            raise errors.InvalidLengthForBrand(brand=card_number.brand, required_length=required_length)
        return card_number

    @staticmethod
    def _get_brand(card_number: str) -> PaymentCardBrand:
        if card_number[0] == '4':
            brand = PaymentCardBrand.visa
        elif 51 <= int(card_number[:2]) <= 55:
            brand = PaymentCardBrand.mastercard
        elif card_number[:2] in {'34', '37'}:
            brand = PaymentCardBrand.amex
        else:
            brand = PaymentCardBrand.other
        return brand


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BYTE SIZE TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BYTE_SIZES = {
    'b': 1,
    'kb': 10**3,
    'mb': 10**6,
    'gb': 10**9,
    'tb': 10**12,
    'pb': 10**15,
    'eb': 10**18,
    'kib': 2**10,
    'mib': 2**20,
    'gib': 2**30,
    'tib': 2**40,
    'pib': 2**50,
    'eib': 2**60,
}
BYTE_SIZES.update({k.lower()[0]: v for k, v in BYTE_SIZES.items() if 'i' not in k})
byte_string_re = re.compile(r'^\s*(\d*\.?\d+)\s*(\w+)?', re.IGNORECASE)


class ByteSize(int):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, int, float]) -> 'ByteSize':

        try:
            return cls(int(v))
        except ValueError:
            pass

        str_match = byte_string_re.match(str(v))
        if str_match is None:
            raise errors.InvalidByteSize()

        scalar, unit = str_match.groups()
        if unit is None:
            unit = 'b'

        try:
            unit_mult = BYTE_SIZES[unit.lower()]
        except KeyError:
            raise errors.InvalidByteSizeUnit(unit=unit)

        return cls(int(float(scalar) * unit_mult))

    def human_readable(self, decimal: bool = False) -> str:

        if decimal:
            divisor = 1000
            units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
            final_unit = 'EB'
        else:
            divisor = 1024
            units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
            final_unit = 'EiB'

        num = float(self)
        for unit in units:
            if abs(num) < divisor:
                return f'{num:0.1f}{unit}'
            num /= divisor

        return f'{num:0.1f}{final_unit}'

    def to(self, unit: str) -> float:

        try:
            unit_div = BYTE_SIZES[unit.lower()]
        except KeyError:
            raise errors.InvalidByteSizeUnit(unit=unit)

        return self / unit_div


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DATE TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if TYPE_CHECKING:
    PastDate = date
    FutureDate = date
else:

    class PastDate(date):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield parse_date
            yield cls.validate

        @classmethod
        def validate(cls, value: date) -> date:
            if value >= date.today():
                raise errors.DateNotInThePastError()

            return value

    class FutureDate(date):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield parse_date
            yield cls.validate

        @classmethod
        def validate(cls, value: date) -> date:
            if value <= date.today():
                raise errors.DateNotInTheFutureError()

            return value


class ConstrainedDate(date):
    gt: Optional[date] = None
    ge: Optional[date] = None
    lt: Optional[date] = None
    le: Optional[date] = None

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        update_not_none(field_schema, exclusiveMinimum=cls.gt, exclusiveMaximum=cls.lt, minimum=cls.ge, maximum=cls.le)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield parse_date
        yield number_size_validator


def condate(
    *,
    gt: date = None,
    ge: date = None,
    lt: date = None,
    le: date = None,
) -> Type[date]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, ge=ge, lt=lt, le=le)
    return type('ConstrainedDateValue', (ConstrainedDate,), namespace)
