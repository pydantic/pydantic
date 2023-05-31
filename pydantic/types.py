from __future__ import annotations as _annotations

import base64
import dataclasses as _dataclasses
import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    FrozenSet,
    Generic,
    Hashable,
    Iterable,
    List,
    Set,
    TypeVar,
    cast,
)
from uuid import UUID

import annotated_types
from pydantic_core import CoreSchema, PydanticCustomError, PydanticKnownError, PydanticOmit, core_schema
from typing_extensions import Annotated, Literal, Protocol

from ._internal import (
    _annotated_handlers,
    _core_metadata,
    _fields,
    _generics,
    _internal_dataclass,
    _known_annotated_metadata,
    _utils,
    _validators,
)
from ._migration import getattr_migration
from .config import ConfigDict
from .errors import PydanticUserError
from .json_schema import JsonSchemaValue

__all__ = (
    'Strict',
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
    'NewPath',
    'Json',
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
    'PastDatetime',
    'FutureDatetime',
    'condate',
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    'SkipValidation',
    'InstanceOf',
    'WithJsonSchema',
)


@_dataclasses.dataclass
class Strict(_fields.PydanticMetadata):
    strict: bool = True

    def __hash__(self) -> int:
        return hash(self.strict)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BOOLEAN TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

StrictBool = Annotated[bool, Strict()]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INTEGER TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def conint(
    *,
    strict: bool | None = None,
    gt: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    le: int | None = None,
    multiple_of: int | None = None,
) -> type[int]:
    return Annotated[  # type: ignore[return-value]
        int,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
    ]


PositiveInt = Annotated[int, annotated_types.Gt(0)]
NegativeInt = Annotated[int, annotated_types.Lt(0)]
NonPositiveInt = Annotated[int, annotated_types.Le(0)]
NonNegativeInt = Annotated[int, annotated_types.Ge(0)]
StrictInt = Annotated[int, Strict()]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FLOAT TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class AllowInfNan(_fields.PydanticMetadata):
    allow_inf_nan: bool = True

    def __hash__(self) -> int:
        return hash(self.allow_inf_nan)


def confloat(
    *,
    strict: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
) -> type[float]:
    return Annotated[  # type: ignore[return-value]
        float,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
        AllowInfNan(allow_inf_nan) if allow_inf_nan is not None else None,
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
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
) -> type[bytes]:
    return Annotated[  # type: ignore[return-value]
        bytes,
        Strict(strict) if strict is not None else None,
        annotated_types.Len(min_length or 0, max_length),
    ]


StrictBytes = Annotated[bytes, Strict()]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STRING TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def constr(
    *,
    strip_whitespace: bool | None = None,
    to_upper: bool | None = None,
    to_lower: bool | None = None,
    strict: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
) -> type[str]:
    return Annotated[  # type: ignore[return-value]
        str,
        Strict(strict) if strict is not None else None,
        annotated_types.Len(min_length or 0, max_length),
        _fields.PydanticGeneralMetadata(
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
    item_type: type[HashableItemType], *, min_length: int | None = None, max_length: int | None = None
) -> type[set[HashableItemType]]:
    return Annotated[  # type: ignore[return-value]
        Set[item_type], annotated_types.Len(min_length or 0, max_length)  # type: ignore[valid-type]
    ]


def confrozenset(
    item_type: type[HashableItemType], *, min_length: int | None = None, max_length: int | None = None
) -> type[frozenset[HashableItemType]]:
    return Annotated[  # type: ignore[return-value]
        FrozenSet[item_type],  # type: ignore[valid-type]
        annotated_types.Len(min_length or 0, max_length),
    ]


AnyItemType = TypeVar('AnyItemType')


def conlist(
    item_type: type[AnyItemType],
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    unique_items: bool | None = None,
) -> type[list[AnyItemType]]:
    """A wrapper around typing.List that adds validation.

    Args:
        item_type (type[AnyItemType]): The type of the items in the list.
        min_length (int | None, optional): The minimum length of the list. Defaults to None.
        max_length (int | None, optional): The maximum length of the list. Defaults to None.
        unique_items (bool | None, optional): Whether the items in the list must be unique. Defaults to None.

    Returns:
        type[list[AnyItemType]]: The wrapped list type.
    """
    if unique_items is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='deprecated-kwargs',
        )
    return Annotated[  # type: ignore[return-value]
        List[item_type],  # type: ignore[valid-type]
        annotated_types.Len(min_length or 0, max_length),
    ]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ IMPORT STRING TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AnyType = TypeVar('AnyType')
if TYPE_CHECKING:
    ImportString = Annotated[AnyType, ...]
else:

    class ImportString:
        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            serializer = core_schema.plain_serializer_function_ser_schema(cls._serialize, when_used='json')
            if cls is source:
                # Treat bare usage of ImportString (`schema is None`) as the same as ImportString[Any]
                return core_schema.no_info_plain_validator_function(
                    function=_validators.import_string, serialization=serializer
                )
            else:
                return core_schema.no_info_before_validator_function(
                    function=_validators.import_string, schema=handler(source), serialization=serializer
                )

        @staticmethod
        def _serialize(v: Any) -> str:
            if isinstance(v, ModuleType):
                return v.__name__
            elif hasattr(v, '__module__') and hasattr(v, '__name__'):
                return f'{v.__module__}.{v.__name__}'
            else:
                return v

        def __repr__(self) -> str:
            return 'ImportString'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DECIMAL TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def condecimal(
    *,
    strict: bool | None = None,
    gt: int | Decimal | None = None,
    ge: int | Decimal | None = None,
    lt: int | Decimal | None = None,
    le: int | Decimal | None = None,
    multiple_of: int | Decimal | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    allow_inf_nan: bool | None = None,
) -> type[Decimal]:
    return Annotated[  # type: ignore[return-value]
        Decimal,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
        _fields.PydanticGeneralMetadata(max_digits=max_digits, decimal_places=decimal_places),
        AllowInfNan(allow_inf_nan) if allow_inf_nan is not None else None,
    ]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UUID TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_internal_dataclass.slots_dataclass
class UuidVersion:
    uuid_version: Literal[1, 3, 4, 5]

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: _annotated_handlers.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.pop('anyOf', None)  # remove the bytes/str union
        field_schema.update(type='string', format=f'uuid{self.uuid_version}')
        return field_schema

    def __get_pydantic_core_schema__(
        self, source: Any, handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.general_after_validator_function(
            cast(core_schema.GeneralValidatorFunction, self.validate), handler(source)
        )

    def validate(self, value: UUID, _: core_schema.ValidationInfo) -> UUID:
        if value.version != self.uuid_version:
            raise PydanticCustomError(
                'uuid_version', 'uuid version {required_version} expected', {'required_version': self.uuid_version}
            )
        return value

    def __hash__(self) -> int:
        return hash(type(self.uuid_version))


UUID1 = Annotated[UUID, UuidVersion(1)]
UUID3 = Annotated[UUID, UuidVersion(3)]
UUID4 = Annotated[UUID, UuidVersion(4)]
UUID5 = Annotated[UUID, UuidVersion(5)]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PATH TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class PathType:
    path_type: Literal['file', 'dir', 'new']

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: _annotated_handlers.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        format_conversion = {'file': 'file-path', 'dir': 'directory-path'}
        field_schema.update(format=format_conversion.get(self.path_type, 'path'), type='string')
        return field_schema

    def __get_pydantic_core_schema__(
        self, source: Any, handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        function_lookup = {
            'file': cast(core_schema.GeneralValidatorFunction, self.validate_file),
            'dir': cast(core_schema.GeneralValidatorFunction, self.validate_directory),
            'new': cast(core_schema.GeneralValidatorFunction, self.validate_new),
        }

        return core_schema.general_after_validator_function(
            function_lookup[self.path_type],
            handler(source),
        )

    @staticmethod
    def validate_file(path: Path, _: core_schema.ValidationInfo) -> Path:
        if path.is_file():
            return path
        else:
            raise PydanticCustomError('path_not_file', 'Path does not point to a file')

    @staticmethod
    def validate_directory(path: Path, _: core_schema.ValidationInfo) -> Path:
        if path.is_dir():
            return path
        else:
            raise PydanticCustomError('path_not_directory', 'Path does not point to a directory')

    @staticmethod
    def validate_new(path: Path, _: core_schema.ValidationInfo) -> Path:
        if path.exists():
            raise PydanticCustomError('path_exists', 'Path already exists')
        elif not path.parent.exists():
            raise PydanticCustomError('parent_does_not_exist', 'Parent directory does not exist')
        else:
            return path

    def __hash__(self) -> int:
        return hash(type(self.path_type))


FilePath = Annotated[Path, PathType('file')]
DirectoryPath = Annotated[Path, PathType('dir')]
NewPath = Annotated[Path, PathType('new')]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ JSON TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if TYPE_CHECKING:
    Json = Annotated[AnyType, ...]  # Json[list[str]] will be recognized by type checkers as list[str]

else:

    class Json:
        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: Any, handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                return core_schema.json_schema(None)
            else:
                return core_schema.json_schema(handler(source))

        def __repr__(self) -> str:
            return 'Json'

        def __hash__(self) -> int:
            return hash(type(self))

        def __eq__(self, other: Any) -> bool:
            return type(other) == type(self)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SECRET TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SecretType = TypeVar('SecretType', str, bytes)


class SecretField(Generic[SecretType]):
    def __init__(self, secret_value: SecretType) -> None:
        self._secret_value: SecretType = secret_value

    def get_secret_value(self) -> SecretType:
        return self._secret_value

    @classmethod
    def __prepare_pydantic_annotations__(
        cls, source: type[Any], annotations: tuple[Any, ...], _config: ConfigDict
    ) -> tuple[Any, Iterable[Any]]:
        metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
        _known_annotated_metadata.check_metadata(metadata, {'min_length', 'max_length'}, cls)
        return (
            source,
            (
                _SecretFieldValidator(source, **metadata),
                *remaining_annotations,
            ),
        )

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.get_secret_value() == other.get_secret_value()

    def __hash__(self) -> int:
        return hash(self.get_secret_value())

    def __len__(self) -> int:
        return len(self._secret_value)

    def __str__(self) -> str:
        return str(self._display())

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._display()!r})'

    def _display(self) -> SecretType:
        raise NotImplementedError


def _secret_display(value: str | bytes) -> str:
    if isinstance(value, bytes):
        value = value.decode()
    return '**********' if value else ''


@_internal_dataclass.slots_dataclass
class _SecretFieldValidator:
    field_type: type[SecretField[Any]]
    min_length: int | None = None
    max_length: int | None = None
    inner_schema: CoreSchema = _dataclasses.field(init=False)

    def validate(self, value: SecretField[SecretType] | SecretType, _: core_schema.ValidationInfo) -> Any:
        error_prefix: Literal['string', 'bytes'] = 'string' if self.field_type is SecretStr else 'bytes'
        if self.min_length is not None and len(value) < self.min_length:
            short_kind: core_schema.ErrorType = f'{error_prefix}_too_short'  # type: ignore[assignment]
            raise PydanticKnownError(short_kind, {'min_length': self.min_length})
        if self.max_length is not None and len(value) > self.max_length:
            long_kind: core_schema.ErrorType = f'{error_prefix}_too_long'  # type: ignore[assignment]
            raise PydanticKnownError(long_kind, {'max_length': self.max_length})

        if isinstance(value, self.field_type):
            return value
        else:
            return self.field_type(value)  # type: ignore[arg-type]

    def serialize(
        self, value: SecretField[SecretType], info: core_schema.SerializationInfo
    ) -> str | SecretField[SecretType]:
        if info.mode == 'json':
            # we want the output to always be string without the `b'` prefix for bytes,
            # hence we just use `secret_display`
            return _secret_display(value.get_secret_value())
        else:
            return value

    def __get_pydantic_json_schema__(
        self, _core_schema: core_schema.CoreSchema, handler: _annotated_handlers.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = self.inner_schema.copy()
        if self.min_length is not None:
            schema['min_length'] = self.min_length  # type: ignore
        if self.max_length is not None:
            schema['max_length'] = self.max_length  # type: ignore
        json_schema = handler(schema)
        _utils.update_not_none(
            json_schema,
            type='string',
            writeOnly=True,
            format='password',
        )
        return json_schema

    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        self.inner_schema = handler(str if self.field_type is SecretStr else bytes)
        error_kind = 'string_type' if self.field_type is SecretStr else 'bytes_type'
        return core_schema.general_after_validator_function(
            self.validate,
            core_schema.union_schema(
                [core_schema.is_instance_schema(self.field_type), self.inner_schema],
                strict=True,
                custom_error_type=error_kind,
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                self.serialize,
                info_arg=True,
                return_schema=core_schema.str_schema(),
                when_used='json',
            ),
        )


class SecretStr(SecretField[str]):
    def _display(self) -> str:
        return _secret_display(self.get_secret_value())


class SecretBytes(SecretField[bytes]):
    def _display(self) -> bytes:
        return _secret_display(self.get_secret_value()).encode()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PAYMENT CARD TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PaymentCardBrand(str, Enum):
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
        self.validate_digits(card_number)

        card_number = self.validate_luhn_check_digit(card_number)

        self.bin = card_number[:6]
        self.last4 = card_number[-4:]
        self.brand = self.validate_brand(card_number)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.general_after_validator_function(
            cls.validate,
            core_schema.str_schema(
                min_length=cls.min_length, max_length=cls.max_length, strip_whitespace=cls.strip_whitespace
            ),
        )

    @classmethod
    def validate(cls, __input_value: str, _: core_schema.ValidationInfo) -> PaymentCardNumber:
        return cls(__input_value)

    @property
    def masked(self) -> str:
        num_masked = len(self) - 10  # len(bin) + len(last4) == 10
        return f'{self.bin}{"*" * num_masked}{self.last4}'

    @classmethod
    def validate_digits(cls, card_number: str) -> None:
        if not card_number.isdigit():
            raise PydanticCustomError('payment_card_number_digits', 'Card number is not all digits')

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
            raise PydanticCustomError('payment_card_number_luhn', 'Card number is not luhn valid')
        return card_number

    @staticmethod
    def validate_brand(card_number: str) -> PaymentCardBrand:
        """
        Validate length based on BIN for major brands:
        https://en.wikipedia.org/wiki/Payment_card_number#Issuer_identification_number_(IIN)
        """
        if card_number[0] == '4':
            brand = PaymentCardBrand.visa
        elif 51 <= int(card_number[:2]) <= 55:
            brand = PaymentCardBrand.mastercard
        elif card_number[:2] in {'34', '37'}:
            brand = PaymentCardBrand.amex
        else:
            brand = PaymentCardBrand.other

        required_length: None | int | str = None
        if brand in PaymentCardBrand.mastercard:
            required_length = 16
            valid = len(card_number) == required_length
        elif brand == PaymentCardBrand.visa:
            required_length = '13, 16 or 19'
            valid = len(card_number) in {13, 16, 19}
        elif brand == PaymentCardBrand.amex:
            required_length = 15
            valid = len(card_number) == required_length
        else:
            valid = True

        if not valid:
            raise PydanticCustomError(
                'payment_card_number_brand',
                'Length for a {brand} card must be {required_length}',
                {'brand': brand, 'required_length': required_length},
            )
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
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.general_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, __input_value: Any, _: core_schema.ValidationInfo) -> ByteSize:
        try:
            return cls(int(__input_value))
        except ValueError:
            pass

        str_match = byte_string_re.match(str(__input_value))
        if str_match is None:
            raise PydanticCustomError('byte_size', 'could not parse value and unit from byte string')

        scalar, unit = str_match.groups()
        if unit is None:
            unit = 'b'

        try:
            unit_mult = BYTE_SIZES[unit.lower()]
        except KeyError:
            raise PydanticCustomError('byte_size_unit', 'could not interpret byte unit: {unit}', {'unit': unit})

        return cls(int(float(scalar) * unit_mult))

    def human_readable(self, decimal: bool = False) -> str:
        if decimal:
            divisor = 1000
            units = 'B', 'KB', 'MB', 'GB', 'TB', 'PB'
            final_unit = 'EB'
        else:
            divisor = 1024
            units = 'B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'
            final_unit = 'EiB'

        num = float(self)
        for unit in units:
            if abs(num) < divisor:
                if unit == 'B':
                    return f'{num:0.0f}{unit}'
                else:
                    return f'{num:0.1f}{unit}'
            num /= divisor

        return f'{num:0.1f}{final_unit}'

    def to(self, unit: str) -> float:
        try:
            unit_div = BYTE_SIZES[unit.lower()]
        except KeyError:
            raise PydanticCustomError('byte_size_unit', 'Could not interpret byte unit: {unit}', {'unit': unit})

        return self / unit_div


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DATE TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _check_annotated_type(annotated_type: str, expected_type: str, annotation: str) -> None:
    if annotated_type != expected_type:
        raise PydanticUserError(f"'{annotation}' cannot annotate '{annotated_type}'.", code='invalid_annotated_type')


if TYPE_CHECKING:
    PastDate = Annotated[date, ...]
    FutureDate = Annotated[date, ...]
else:

    class PastDate:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.date_schema(now_op='past')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'date', cls.__name__)
                schema['now_op'] = 'past'
                return schema

        def __repr__(self) -> str:
            return 'PastDate'

    class FutureDate:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.date_schema(now_op='future')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'date', cls.__name__)
                schema['now_op'] = 'future'
                return schema

        def __repr__(self) -> str:
            return 'FutureDate'


def condate(
    *,
    strict: bool | None = None,
    gt: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    le: date | None = None,
) -> type[date]:
    return Annotated[  # type: ignore[return-value]
        date,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
    ]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DATETIME TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if TYPE_CHECKING:
    AwareDatetime = Annotated[datetime, ...]
    NaiveDatetime = Annotated[datetime, ...]
    PastDatetime = Annotated[datetime, ...]
    FutureDatetime = Annotated[datetime, ...]

else:

    class AwareDatetime:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(tz_constraint='aware')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['tz_constraint'] = 'aware'
                return schema

        def __repr__(self) -> str:
            return 'AwareDatetime'

    class NaiveDatetime:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(tz_constraint='naive')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['tz_constraint'] = 'naive'
                return schema

        def __repr__(self) -> str:
            return 'NaiveDatetime'

    class PastDatetime:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(now_op='past')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['now_op'] = 'past'
                return schema

        def __repr__(self) -> str:
            return 'PastDatetime'

    class FutureDatetime:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(now_op='future')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['now_op'] = 'future'
                return schema

        def __repr__(self) -> str:
            return 'FutureDatetime'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Encoded TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class EncoderProtocol(Protocol):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        """Can throw `PydanticCustomError`"""
        ...

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        ...

    @classmethod
    def get_json_format(cls) -> str:
        ...


class Base64Encoder(EncoderProtocol):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        try:
            return base64.decodebytes(data)
        except ValueError as e:
            raise PydanticCustomError('base64_decode', "Base64 decoding error: '{error}'", {'error': str(e)})

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return base64.encodebytes(value)

    @classmethod
    def get_json_format(cls) -> str:
        return 'base64'


@_internal_dataclass.slots_dataclass
class EncodedBytes:
    encoder: type[EncoderProtocol]

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: _annotated_handlers.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.update(type='string', format=self.encoder.get_json_format())
        return field_schema

    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        return core_schema.general_after_validator_function(
            function=self.decode,
            schema=core_schema.bytes_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(function=self.encode),
        )

    def decode(self, data: bytes, _: core_schema.ValidationInfo) -> bytes:
        return self.encoder.decode(data)

    def encode(self, value: bytes) -> bytes:
        return self.encoder.encode(value)

    def __hash__(self) -> int:
        return hash(self.encoder)


class EncodedStr(EncodedBytes):
    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        return core_schema.general_after_validator_function(
            function=self.decode_str,
            schema=super().__get_pydantic_core_schema__(source=source, handler=handler),
            serialization=core_schema.plain_serializer_function_ser_schema(function=self.encode_str),
        )

    def decode_str(self, data: bytes, _: core_schema.ValidationInfo) -> str:
        return data.decode()

    def encode_str(self, value: str) -> str:
        return super().encode(value=value.encode()).decode()


Base64Bytes = Annotated[bytes, EncodedBytes(encoder=Base64Encoder)]
Base64Str = Annotated[str, EncodedStr(encoder=Base64Encoder)]


if TYPE_CHECKING:
    # If we add configurable attributes to IsInstance, we'd probably need to stop hiding it from type checkers like this
    InstanceOf = Annotated[AnyType, ...]  # `IsInstance[Sequence]` will be recognized by type checkers as `Sequence`

else:

    @_internal_dataclass.slots_dataclass
    class InstanceOf:
        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: Any, handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            from pydantic import PydanticSchemaGenerationError

            # use the generic _origin_ as the second argument to isinstance when appropriate
            python_schema = core_schema.is_instance_schema(_generics.get_origin(source) or source)

            try:
                # Try to generate the "standard" schema, which will be used when loading from JSON
                json_schema = handler(source)
            except PydanticSchemaGenerationError:
                # If that fails, just produce a schema that can validate from python
                return python_schema
            else:
                return core_schema.json_or_python_schema(python_schema=python_schema, json_schema=json_schema)


__getattr__ = getattr_migration(__name__)


@_internal_dataclass.slots_dataclass
class WithJsonSchema:
    """
    Add this as an annotation on a field to override the (base) JSON schema that would be generated for that field.

    This provides a way to set a JSON schema for types that would otherwise raise errors when producing a JSON schema,
    such as Callable, or types that have an is-instance core schema, without needing to go so far as creating a
    custom subclass of pydantic.json_schema.GenerateJsonSchema.

    Note that any _modifications_ to the schema that would normally be made (such as setting the title for model fields)
    will still be performed.
    """

    json_schema: JsonSchemaValue | None

    def __get_pydantic_json_schema__(
        self, _core_schema: core_schema.CoreSchema, handler: _annotated_handlers.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        if self.json_schema is None:
            # This exception is handled in pydantic.json_schema.GenerateJsonSchema._named_required_fields_schema
            raise PydanticOmit
        else:
            return self.json_schema


if TYPE_CHECKING:
    SkipValidation = Annotated[AnyType, ...]  # SkipValidation[list[str]] will be treated by type checkers as list[str]
else:

    @_internal_dataclass.slots_dataclass
    class SkipValidation:
        """
        If this is applied as an annotation (e.g., via `x: Annotated[int, SkipValidation]`), validation will be skipped.
        You can also use `SkipValidation[int]` as a shorthand for `Annotated[int, SkipValidation]`.

        This can be useful if you want to use a type annotation for documentation/IDE/type-checking purposes,
        and know that it is safe to skip validation for one or more of the fields.

        Because this converts the validation schema to `any_schema`, subsequent annotation-applied transformations
        may not have the expected effects. Therefore, when used, this annotation should generally be the final
        annotation applied to a type.
        """

        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, SkipValidation()]

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: Any, handler: _annotated_handlers.GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            original_schema = handler.generate_schema(source)
            metadata = _core_metadata.build_metadata_dict(js_functions=[lambda _c, h: h(original_schema)])
            return core_schema.any_schema(metadata=metadata, serialization=original_schema)


@_internal_dataclass.slots_dataclass
class TransformSchema:
    """
    An annotation that can be used to apply a transform to a core schema.
    """

    transform: Callable[[CoreSchema], CoreSchema]

    def __get_pydantic_core_schema__(
        self, source_type: type[Any], handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> CoreSchema:
        return self.transform(handler(source_type))
