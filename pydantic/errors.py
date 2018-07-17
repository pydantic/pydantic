from decimal import Decimal
from pathlib import Path
from typing import Union

from .utils import display_as_type


class PydanticErrorMixin:
    code: str
    msg_template: str

    def __init__(self, **ctx) -> None:
        self.ctx = ctx or None
        super().__init__()

    def __str__(self) -> str:
        return self.msg_template.format(**self.ctx or {})


class PydanticTypeError(PydanticErrorMixin, TypeError):
    pass


class PydanticValueError(PydanticErrorMixin, ValueError):
    pass


class ConfigError(RuntimeError):
    pass


class MissingError(PydanticValueError):
    msg_template = 'field required'


class ExtraError(PydanticValueError):
    msg_template = 'extra fields not permitted'


class NoneIsNotAllowedError(PydanticTypeError):
    code = 'none.not_allowed'
    msg_template = 'none is not an allow value'


class BytesError(PydanticTypeError):
    msg_template = 'byte type expected'


class DictError(PydanticTypeError):
    msg_template = 'value is not a valid dict'


class DSNDriverIsEmptyError(PydanticValueError):
    code = 'dsn.driver_is_empty'
    msg_template = '"driver" field may not be empty'


class EmailError(PydanticValueError):
    msg_template = 'value is not a valid email address'


class EnumError(PydanticTypeError):
    msg_template = 'value is not a valid enumeration member'


class IntegerError(PydanticTypeError):
    msg_template = 'value is not a valid integer'


class FloatError(PydanticTypeError):
    msg_template = 'value is not a valid float'


class PathError(PydanticTypeError):
    msg_template = 'value is not a valid path'


class _PathValueError(PydanticValueError):
    def __init__(self, *, path: Path) -> None:
        super().__init__(path=str(path))


class PathNotExistsError(_PathValueError):
    code = 'path.not_exists'
    msg_template = 'file or directory at path "{path}" does not exist'


class PathNotAFileError(_PathValueError):
    code = 'path.not_a_file'
    msg_template = 'path "{path}" does not point to a file'


class PathNotADirectoryError(_PathValueError):
    code = 'path.not_a_directory'
    msg_template = 'path "{path}" does not point to a directory'


class PyObjectError(PydanticTypeError):
    msg_template = 'ensure this value contains valid import path'


class ListError(PydanticTypeError):
    msg_template = 'value is not a valid list'


class SetError(PydanticTypeError):
    msg_template = 'value is not a valid set'


class TupleError(PydanticTypeError):
    msg_template = 'value is not a valid tuple'


class TupleLengthError(PydanticValueError):
    code = 'tuple.length'
    msg_template = 'wrong tuple length {actual_length}, expected {expected_length}'

    def __init__(self, *, actual_length: int, expected_length: int) -> None:
        super().__init__(actual_length=actual_length, expected_length=expected_length)


class AnyStrMinLengthError(PydanticValueError):
    code = 'any_str.min_length'
    msg_template = 'ensure this value has at least {limit_value} characters'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)


class AnyStrMaxLengthError(PydanticValueError):
    code = 'any_str.max_length'
    msg_template = 'ensure this value has at most {limit_value} characters'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)


class StrError(PydanticTypeError):
    msg_template = 'str type expected'


class StrRegexError(PydanticValueError):
    code = 'str.regex'
    msg_template = 'string does not match regex "{pattern}"'

    def __init__(self, *, pattern: str) -> None:
        super().__init__(pattern=pattern)


class _NumberBoundError(PydanticValueError):
    def __init__(self, *, limit_value: Union[int, float, Decimal]) -> None:
        super().__init__(limit_value=limit_value)


class NumberNotGtError(_NumberBoundError):
    code = 'number.not_gt'
    msg_template = 'ensure this value is greater than {limit_value}'


class NumberNotGeError(_NumberBoundError):
    code = 'number.not_ge'
    msg_template = 'ensure this value is greater than or equal to {limit_value}'


class NumberNotLtError(_NumberBoundError):
    code = 'number.not_lt'
    msg_template = 'ensure this value is less than {limit_value}'


class NumberNotLeError(_NumberBoundError):
    code = 'number.not_le'
    msg_template = 'ensure this value is less than or equal to {limit_value}'


class DecimalError(PydanticTypeError):
    msg_template = 'value is not a valid decimal'


class DecimalIsNotFiniteError(PydanticValueError):
    code = 'decimal.not_finite'
    msg_template = 'value is not a valid decimal'


class DecimalMaxDigitsError(PydanticValueError):
    code = 'decimal.max_digits'
    msg_template = 'ensure that there are no more than {max_digits} digits in total'

    def __init__(self, *, max_digits: int) -> None:
        super().__init__(max_digits=max_digits)


class DecimalMaxPlacesError(PydanticValueError):
    code = 'decimal.max_places'
    msg_template = 'ensure that there are no more than {decimal_places} decimal places'

    def __init__(self, *, decimal_places: int) -> None:
        super().__init__(decimal_places=decimal_places)


class DecimalWholeDigitsError(PydanticValueError):
    code = 'decimal.whole_digits'
    msg_template = 'ensure that there are no more than {whole_digits} digits before the decimal point'

    def __init__(self, *, whole_digits: int) -> None:
        super().__init__(whole_digits=whole_digits)


class DateTimeError(PydanticTypeError):
    msg_template = 'invalid datetime format'


class DateError(PydanticTypeError):
    msg_template = 'invalid date format'


class TimeError(PydanticTypeError):
    msg_template = 'invalid time format'


class DurationError(PydanticTypeError):
    msg_template = 'invalid duration format'


class UUIDError(PydanticTypeError):
    msg_template = 'value is not a valid uuid'


class UUIDVersionError(PydanticValueError):
    code = 'uuid.version'
    msg_template = 'uuid version {required_version} expected'

    def __init__(self, *, required_version: int) -> None:
        super().__init__(required_version=required_version)


class ArbitraryTypeError(PydanticTypeError):
    code = 'arbitrary_type'
    msg_template = 'instance of {expected_arbitrary_type} expected'

    def __init__(self, *, expected_arbitrary_type) -> None:
        super().__init__(expected_arbitrary_type=display_as_type(expected_arbitrary_type))


class JsonError(PydanticValueError):
    msg_template = 'Invalid JSON'


class JsonTypeError(PydanticTypeError):
    code = 'json'
    msg_template = 'JSON object must be str, bytes or bytearray'
