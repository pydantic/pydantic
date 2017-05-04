from collections import OrderedDict
from functools import partial, wraps
from inspect import signature
from pathlib import Path
from typing import Any, Callable, Dict, List, Type


def str_validator(v) -> str:  # TODO config
    if isinstance(v, str):
        return v
    elif isinstance(v, bytes):
        return v.decode()
    return str(v)


def bytes_validator(v) -> bytes:
    if isinstance(v, bytes):
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


def number_size_validator(v, *, config):
    if config.min_number_size <= v <= config.max_number_size:
        raise ValueError(f'size not in range {config.min_number_size} to {config.max_number_size}')
    return v


def anystr_length_validator(v, *, config):
    if config.max_anystr_length <= len(v) <= config.max_anystr_length:
        raise ValueError(f'length not in range {config.max_anystr_length} to {config.max_anystr_length}')
    return v


class ValidatorsLookup:
    def __init__(self):
        self._validators_lookup: Dict[Type, List[Callable]] = {
            int: [int, number_size_validator],
            float: [float, number_size_validator],
            Path: [Path],
            str: [str_validator, anystr_length_validator],
            bytes: [bytes_validator, anystr_length_validator],
            bool: [bool_validator],
            # TODO list, List, Dict, Union, datetime, date, time, custom types
        }
        self._validators_lookup_subclasses = []

    def find(self, type_):
        try:
            return self._validators_lookup[type_]
        except KeyError:
            raise RuntimeError(f'no validator found for {type_}')

    def register(self, type_, *validators_):
        self._validators_lookup[type_] = list(validators_)


validators_lookup = ValidatorsLookup()


def wrap_validator(func, config):
    multi = False
    try:
        multi = len(signature(func).parameters) > 1
    except ValueError:
        # happens on builtins like float
        pass
    if multi:
        return wraps(func)(partial(func, config=config))
    return func


class Field:
    __slots__ = 'type_', 'validators', 'default', 'required', 'name', 'description', 'info'

    def __init__(
            self, *,
            type_: Type,
            validators: List[Callable]=None,
            default: Any=None,
            required: bool=False,
            name: str=None,
            description: str=None):

        if default and required:
            raise RuntimeError('It doesn\'t make sense to have `default` set and `required=True`.')

        self.type_ = type_
        self.validators = validators
        self.default = default
        self.required = required
        self.name = name
        self.description = description

    def prepare(self, name, config, class_validators):
        self.name = self.name or name
        if self.default and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise RuntimeError(f'unable to infer type for {self.name}')

        override_validator = class_validators.get(f'validate_{self.name}_override')
        if override_validator:
            self.validators = [override_validator]

        self.validators = self.validators or self._find_validator()

        self.validators.insert(0, class_validators.get(f'validate_{self.name}_pre'))
        self.validators.append(class_validators.get(f'validate_{self.name}'))
        self.validators.append(class_validators.get(f'validate_{self.name}_post'))

        self.validators = tuple(wrap_validator(v, config) for v in self.validators if v)
        self.info = OrderedDict([
            ('type', self.type_.__name__),
            ('default', self.default),
            ('required', self.required),
            ('validators', [f.__qualname__ for f in self.validators])
        ])
        if self.required:
            self.info.pop('default')
        if self.description:
            self.info['description'] = self.description

    def _find_validator(self):
        get_validators = getattr(self.type_, 'get_validators', None)
        if get_validators:
            return list(get_validators())
        return validators_lookup.find(self.type_)

    def validate(self, v):
        for validator in self.validators:
            v = validator(v)
        return v

    @classmethod
    def infer(cls, *, name, value, annotation, config, class_validators):
        required = value == Ellipsis
        instance = cls(
            type_=annotation,
            default=None if required else value,
            required=required
        )
        instance.prepare(name, config, class_validators)
        return instance

    def __repr__(self):
        return f'<Field: {self}>'

    def __str__(self):
        return ', '.join(f'{k}={v!r}' for k, v in self.info.items())


class EnvField(Field):
    def __init__(self, *, env=None, **kwargs):
        super().__init__(**kwargs)
        self.env_var_name = env
