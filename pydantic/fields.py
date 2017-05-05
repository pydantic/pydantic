import inspect
from collections import OrderedDict
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, List, Optional, Type

from .exceptions import ConfigError

NoneType = type(None)


def not_none_validator(v):
    if v is None:
        raise TypeError('None is not an allow value')
    return v


def str_validator(v) -> str:
    if isinstance(v, (str, NoneType)):
        return v
    elif isinstance(v, bytes):
        return v.decode()
    return str(v)


def bytes_validator(v) -> bytes:
    if isinstance(v, (bytes, NoneType)):
        return v
    return str_validator(v).encode()


BOOL_STRINGS = {
    '1',
    'TRUE',
    'ON',
}


def bool_validator(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, bytes):
        v = v.decode()
    if isinstance(v, str):
        return v.upper() in BOOL_STRINGS
    return bool(v)


def number_size_validator(v, m):
    if m.config.min_number_size <= v <= m.config.max_number_size:
        return v
    raise ValueError(f'size not in range {m.config.min_number_size} to {m.config.max_number_size}')


def anystr_length_validator(v, m):
    if v is None or m.config.min_anystr_length <= len(v) <= m.config.max_anystr_length:
        return v
    raise ValueError(f'length not in range {m.config.max_anystr_length} to {m.config.max_anystr_length}')


def dict_validator(v) -> dict:
    if isinstance(v, dict):
        return v
    return dict(v)


VALIDATORS_LOOKUP = {
    int: [int, number_size_validator],
    float: [float, number_size_validator],
    bool: [bool_validator],

    Path: [Path],

    # TODO could do this better by detecting option Unions, removing not_none_validator and dealing with it directly
    Optional[str]: [str_validator, anystr_length_validator],
    str: [not_none_validator, str_validator, anystr_length_validator],

    Optional[bytes]: [bytes_validator, anystr_length_validator],
    bytes: [not_none_validator, bytes_validator, anystr_length_validator],

    dict: [not_none_validator, dict_validator]

    # TODO list, List, Dict, Union, datetime, date, time, custom types
}


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_MODEL = 2


class Field:
    __slots__ = 'type_', 'validators', 'default', 'required', 'name', 'description', 'info', 'validate_always'

    def __init__(
            self, *,
            type_: Type,
            validators: List[Callable]=None,
            default: Any=None,
            required: bool=False,
            name: str=None,
            description: str=None):

        if default and required:
            raise ConfigError("It doesn't make sense to have `default` set and `required=True`.")

        self.type_ = type_
        self.validate_always = getattr(self.type_, 'validate_always', False)
        self.validators = validators
        self.default = default
        self.required = required
        self.name = name
        self.description = description

    def prepare(self, name, class_validators):
        self.name = self.name or name
        if self.default and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise ConfigError(f'unable to infer type for attribute "{self.name}"')

        override_validator = class_validators.get(f'validate_{self.name}_override')
        if override_validator:
            self.validators = [override_validator]

        self.validators = self.validators or self._find_validator()

        self.validators.insert(0, class_validators.get(f'validate_{self.name}_pre'))
        self.validators.append(class_validators.get(f'validate_{self.name}'))
        self.validators.append(class_validators.get(f'validate_{self.name}_post'))

        self.validators = tuple(self._process_validator(v) for v in self.validators if v)
        self.info = OrderedDict([
            ('type', self._type_name),
            ('default', self.default),
            ('required', self.required),
            ('validators', [f[1].__qualname__ for f in self.validators])
        ])
        if self.required:
            self.info.pop('default')
        if self.description:
            self.info['description'] = self.description

    @property
    def _type_name(self):
        try:
            return self.type_.__name__
        except AttributeError:
            # happens with unions
            return str(self.type_)

    def _find_validator(self):
        get_validators = getattr(self.type_, 'get_validators', None)
        if get_validators:
            return list(get_validators())
        try:
            return VALIDATORS_LOOKUP[self.type_]
        except KeyError:
            raise ConfigError(f'no validator found for {self.type_}')

    @classmethod
    def _process_validator(cls, validator):
        try:
            signature = inspect.signature(validator)
        except ValueError:
            # happens on builtins like float
            return ValidatorSignature.JUST_VALUE, validator

        try:
            return ValidatorSignature(len(signature.parameters)), validator
        except ValueError as e:
            raise ConfigError(f'Invalid signature for validator {validator}: {signature}, should be: '
                              f'(value), (value, model)') from e

    def validate(self, v, model):
        for signature, validator in self.validators:
            try:
                if signature == ValidatorSignature.JUST_VALUE:
                    v = validator(v)
                else:
                    v = validator(v, model)
            except (ValueError, TypeError, ImportError) as e:
                return v, validator, e
        return v, None, None

    @classmethod
    def infer(cls, *, name, value, annotation, class_validators):
        required = value == Ellipsis
        instance = cls(
            type_=annotation,
            default=None if required else value,
            required=required
        )
        instance.prepare(name, class_validators)
        return instance

    def __repr__(self):
        return f'<Field {self}>'

    def __str__(self):
        return f'{self.name}: ' + ', '.join(f'{k}={v!r}' for k, v in self.info.items())
