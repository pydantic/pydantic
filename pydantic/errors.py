__all__ = (
    'PydanticErrorMixin',
    'PydanticTypeError',
    'PydanticValueError',

    'ConfigError',

    'MissingError',
    'ExtraError',

    'IntegerError',
    'FloatError',

    'DecimalError',
    'DecimalIsNotFiniteError',
    'DecimalMaxDigitsError',
    'DecimalMaxPlacesError',
    'DecimalWholeDigitsError',

    'UUIDError',
    'UUIDVersionError',
)


class PydanticErrorMixin:
    msg_template: str

    def __init__(self, **ctx):
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
    msg_template = 'field required'


class ExtraError(PydanticValueError):
    msg_template = 'extra fields not permitted'


class IntegerError(PydanticTypeError):
    msg_template = 'value is not a valid integer'


class FloatError(PydanticTypeError):
    msg_template = 'value is not a valid float'


class DecimalError(PydanticTypeError):
    msg_template = 'value is not a valid decimal'


class DecimalIsNotFiniteError(PydanticValueError):
    msg_template = 'value is not a valid decimal'


class DecimalMaxDigitsError(PydanticValueError):
    msg_template = 'ensure that there are no more than {max_digits} digits in total'

    def __init__(self, *, max_digits: int) -> None:
        super().__init__(max_digits=max_digits)


class DecimalMaxPlacesError(PydanticValueError):
    msg_template = 'ensure that there are no more than {decimal_places} decimal places'

    def __init__(self, *, decimal_places: int) -> None:
        super().__init__(decimal_places=decimal_places)


class DecimalWholeDigitsError(PydanticValueError):
    msg_template = 'ensure that there are no more than {whole_digits} digits before the decimal point'

    def __init__(self, *, whole_digits: int) -> None:
        super().__init__(whole_digits=whole_digits)


class UUIDError(PydanticTypeError):
    msg_template = 'value is not a valid uuid'


class UUIDVersionError(PydanticValueError):
    msg_template = 'uuid version {required_version} expected'

    def __init__(self, *, required_version: int) -> None:
        super().__init__(required_version=required_version)
