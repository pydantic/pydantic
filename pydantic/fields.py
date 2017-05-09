import inspect
from collections import OrderedDict
from enum import IntEnum
from typing import Any, Mapping, Sequence, Type, Union  # noqa

from .exceptions import ConfigError, Error, type_json
from .validators import NoneType, find_validators, not_none_validator


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_KWARGS = 2
    BOUND_METHOD = 3


class Shape(IntEnum):
    SINGLETON = 1
    MULTIPART = 2
    SEQUENCE = 3
    MAPPING = 4


class Field:
    __slots__ = ('type_', 'key_type_', 'sub_fields', 'key_field', 'validators', 'default',
                 'required', 'name', 'description', 'info', 'validate_always', 'allow_none', 'shape')

    def __init__(
            self, *,
            name: str=None,
            type_: Type,
            class_validators: dict=None,
            default: Any=None,
            required: bool=False,
            description: str=None):

        self.name: str = name
        self.type_: type = type_
        self.key_type_: type = None
        self.validate_always: bool = getattr(self.type_, 'validate_always', False)
        self.sub_fields = []
        self.key_field: Field = None
        self.validators = []
        self.default: Any = default
        self.required: bool = required
        self.description: str = description
        self.allow_none: bool = False
        self.shape: Shape = Shape.SINGLETON
        self._prepare(class_validators or {})

    @classmethod
    def infer(cls, *, name, value, annotation, class_validators):
        required = value == Ellipsis
        return cls(
            type_=annotation,
            class_validators=class_validators,
            default=None if required else value,
            required=required,
            name=name
        )

    def _prepare(self, class_validators):
        if self.default and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise ConfigError(f'unable to infer type for attribute "{self.name}"')

        if not self.required and not self.validate_always and self.default is None:
            self.allow_none = True

        self._populate_sub_fields(self.type_, class_validators)
        if self.key_type_:
            self.key_field = self._get_sub_field(
                self.key_type_,
                class_validators=class_validators,
                name=f'key_{self.name}'
            )

        self.info = OrderedDict([
            ('type', type_json(self.type_)),
            ('default', self.default),
            ('required', self.required)
        ])
        if self.required:
            self.info.pop('default')
        if self.shape == Shape.MULTIPART:
            self.info['sub_fields'] = [f for f in self.sub_fields]
        else:
            self.info['validators'] = [v[1].__qualname__ for v in self.validators]

        # TODO
        # if self.description:
        #     self.info['description'] = self.description

    def _populate_sub_fields(self, type_, class_validators):
        # typing interface is horrible, we have to do some ugly checks
        origin = getattr(self.type_, '__origin__', None)
        if origin:
            if origin is Union:
                types_ = []
                for type_ in type_.__args__:
                    if type_ is NoneType:
                        self.allow_none = True
                    else:
                        types_.append(type_)
                self.sub_fields = [self._get_sub_field(t, class_validators=class_validators) for t in types_]
                self.shape = Shape.MULTIPART
                return
            elif issubclass(origin, Sequence):
                self.type_ = self.type_.__args__[0]
                self.shape = Shape.SEQUENCE
            else:
                assert issubclass(origin, Mapping)
                self.key_type_ = self.type_.__args__[0]
                self.type_ = self.type_.__args__[1]
                self.shape = Shape.MAPPING

        get_validators = getattr(self.type_, 'get_validators', None)
        if get_validators:
            v_funcs = list(get_validators())
        else:
            v_funcs = find_validators(self.type_)

        v_funcs.insert(0, class_validators.get(f'validate_{self.name}_pre'))
        v_funcs.append(class_validators.get(f'validate_{self.name}'))
        v_funcs.append(class_validators.get(f'validate_{self.name}_post'))
        for f in v_funcs:
            if not f:
                continue
            if self.allow_none and f is not_none_validator:
                continue
            self.validators.append((
                _get_validator_signature(f),
                f,
            ))

    def _get_sub_field(self, type_, class_validators, name=None):
        return Field(
            type_=type_,
            class_validators=class_validators,
            default=self.default,
            required=self.required,
            name=name or self.name
        )

    def _find_validators(self):
        get_validators = getattr(self.type_, 'get_validators', None)
        if get_validators:
            return list(get_validators())
        return find_validators(self.type_)

    def validate(self, v, model):
        if self.allow_none and v is None:
            return None, None

        if self.shape is Shape.SINGLETON or self.shape is Shape.MULTIPART:
            return self._validate_singleton(v, model)
        elif self.shape is Shape.SEQUENCE:
            return self._validate_sequence(v, model)
        else:
            return self._validate_mapping(v, model)

    def _validate_sequence(self, v, model):
        result, errors = [], []
        try:
            v_iter = enumerate(v)
        except TypeError as exc:
            return v, Error(exc, None, None)
        for i, v_ in v_iter:
            single_result, single_errors = self._validate_singleton(v_, model, i)
            if errors or single_errors:
                errors.append(single_errors)
            else:
                result.append(single_result)
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_mapping(self, v, model):
        if isinstance(v, dict):
            v_iter = v
        else:
            try:
                v_iter = dict(v)
            except TypeError as exc:
                return v, Error(exc, None, None)

        result, errors = {}, []
        for k, v_ in v_iter.items():
            key_result, key_errors = self.key_field.validate(v, model)
            value_result, value_errors = self._validate_singleton(v_, model, k)

            if errors or value_errors or key_errors:
                errors.append([key_errors, value_errors])
            else:
                result[key_result] = value_result
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_singleton(self, v, model, index=None):
        if self.shape == Shape.SINGLETON:
            for signature, validator in self.validators:
                try:
                    if signature is ValidatorSignature.JUST_VALUE:
                        v = validator(v)
                    elif signature is ValidatorSignature.VALUE_KWARGS:
                        v = validator(v, model=model, field=self)
                    else:
                        v = validator(model, v)
                except (ValueError, TypeError) as exc:
                    return v, Error(exc, self.type_, index)
            return v, None

        errors = []
        for field in self.sub_fields:
            value, error = field.validate(v, model)
            if error:
                errors.append(error)
            else:
                return value, None
        return v, errors

    def __repr__(self):
        return f'<Field {self}>'

    def __str__(self):
        return f'{self.name}: ' + ', '.join(f'{k}={v!r}' for k, v in self.info.items())


def _get_validator_signature(validator):
    try:
        signature = inspect.signature(validator)
    except ValueError:
        # happens on builtins like float
        return ValidatorSignature.JUST_VALUE

    # bind here will raise a TypeError so:
    # 1. we can deal with it before validation begins
    # 2. (more importantly) it doesn't get confused with a TypeError when evaluating the validator
    try:
        if list(signature.parameters)[0] == 'self':
            signature.bind(object(), 1)
            return ValidatorSignature.BOUND_METHOD
        elif len(signature.parameters) == 1:
            signature.bind(1)
            return ValidatorSignature.JUST_VALUE
        else:
            signature.bind(1, model=2, field=3)
            return ValidatorSignature.VALUE_KWARGS
    except TypeError as e:
        raise ConfigError(f'Invalid signature for validator {validator}: {signature}, should be: '
                          f'(value) or (value, *, model, field)') from e
