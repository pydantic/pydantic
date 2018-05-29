from decimal import Decimal
from typing import Union

__all__ = (
    'PydanticErrorMixin',
    'PydanticTypeError',
    'PydanticValueError',

    'ConfigError',

    'MissingError',
    'ExtraError',

    'NoneIsNotAllowedError',

    'EnumError',
    'IntegerError',
    'FloatError',
    'PathError',

    'NumberMinSizeError',
    'NumberMaxSizeError',

    'DecimalError',
    'DecimalIsNotFiniteError',
    'DecimalMaxDigitsError',
    'DecimalMaxPlacesError',
    'DecimalWholeDigitsError',

    'UUIDError',
    'UUIDVersionError',
)


class PydanticErrorMixin:
    code: str
    msg_template: str

    def __init__(self, **ctx) -> None:
        self.ctx = ctx or None
        super().__init__()

    def __str__(self) -> str:
        return self.msg_template.format(**self.ctx or {})


class PydanticTypeError(PydanticErrorMixin,
                        TypeError):
    pass


class PydanticValueError(PydanticErrorMixin,
                         ValueError):
    pass


class ConfigError(RuntimeError):
    pass


class MissingError(PydanticValueError):
    code = 'missing'
    msg_template = 'field required'


class ExtraError(PydanticValueError):
    code = 'extra'
    msg_template = 'extra fields not permitted'


class NoneIsNotAllowedError(PydanticTypeError):
    code = 'none.not_allowed'
    msg_template = 'none is not an allow value'


class EnumError(PydanticTypeError):
    code = 'enum'
    msg_template = 'value is not a valid enumeration member'


class IntegerError(PydanticTypeError):
    code = 'integer'
    msg_template = 'value is not a valid integer'


class FloatError(PydanticTypeError):
    code = 'float'
    msg_template = 'value is not a valid float'


class PathError(PydanticTypeError):
    code = 'path'
    msg_template = 'value is not a valid path'


class NumberMinSizeError(PydanticValueError):
    code = 'number.min_size'
    msg_template = 'ensure this value is greater than {limit_value}'

    def __init__(self, *, limit_value: Union[int, float, Decimal]) -> None:
        super().__init__(limit_value=limit_value)


class NumberMaxSizeError(PydanticValueError):
    code = 'number.max_size'
    msg_template = 'ensure this value is less than {limit_value}'

    def __init__(self, *, limit_value: Union[int, float, Decimal]) -> None:
        super().__init__(limit_value=limit_value)


class DecimalError(PydanticTypeError):
    code = 'decimal'
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


class UUIDError(PydanticTypeError):
    code = 'uuid'
    msg_template = 'value is not a valid uuid'


class UUIDVersionError(PydanticValueError):
    code = 'uuid.version'
    msg_template = 'uuid version {required_version} expected'

    def __init__(self, *, required_version: int) -> None:
        super().__init__(required_version=required_version)
