import inspect
from collections import OrderedDict
from enum import IntEnum
from typing import Any, List, Mapping, Set, Type, Union

from .exceptions import ConfigError, Error, type_display
from .validators import NoneType, find_validators, not_none_validator

Required: Any = Ellipsis


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_KWARGS = 2


class Shape(IntEnum):
    SINGLETON = 1
    LIST = 2
    SET = 3
    MAPPING = 4


class Field:
    __slots__ = ('type_', 'key_type_', 'sub_fields', 'key_field', 'validators', 'default', 'required', 'model_config',
                 'name', 'alias', 'description', 'info', 'validate_always', 'allow_none', 'shape', 'multipart')

    def __init__(
            self, *,
            name: str,
            type_: Type,
            alias: str=None,
            class_validators: dict=None,
            default: Any=None,
            required: bool=False,
            allow_none: bool=False,
            model_config: Any=None,
            description: str=None):

        self.name: str = name
        self.alias: str = alias or name
        self.type_: type = type_
        self.key_type_: type = None
        self.validate_always: bool = getattr(self.type_, 'validate_always', False)
        self.sub_fields = None
        self.key_field: Field = None
        self.validators = []
        self.default: Any = default
        self.required: bool = required
        self.model_config = model_config
        self.description: str = description
        self.allow_none: bool = allow_none
        self.shape: Shape = Shape.SINGLETON
        self.multipart = False
        self.info = {}
        self._prepare(class_validators or {})

    @classmethod
    def infer(cls, *, name, value, annotation, class_validators, config):
        required = value == Required
        field_config = _get_field_config(config, name)
        return cls(
            name=name,
            type_=annotation,
            alias=field_config and field_config.get('alias'),
            class_validators=class_validators,
            default=None if required else value,
            required=required,
            model_config=config,
            description=field_config and field_config.get('description'),
        )

    def set_config(self, config):
        self.model_config = config
        field_config = _get_field_config(config, self.name)
        if field_config:
            self.alias = field_config.get('alias') or self.alias
            self.description = field_config.get('description') or self.description

    @property
    def alt_alias(self):
        return self.name != self.alias

    def _prepare(self, class_validators):
        if self.default is not None and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise ConfigError(f'unable to infer type for attribute "{self.name}"')

        if not self.required and not self.validate_always and self.default is None:
            self.allow_none = True

        self._populate_sub_fields(class_validators)
        if self.sub_fields is None:
            self._populate_validators(class_validators)

        self.info = OrderedDict([
            ('type', type_display(self.type_)),
            ('default', self.default),
            ('required', self.required)
        ])
        if self.required:
            self.info.pop('default')
        if self.multipart:
            self.info['sub_fields'] = self.sub_fields
        else:
            self.info['validators'] = [v[1].__qualname__ for v in self.validators]

        # TODO
        # if self.description:
        #     self.info['description'] = self.description

    def _populate_sub_fields(self, class_validators):
        # typing interface is horrible, we have to do some ugly checks
        origin = getattr(self.type_, '__origin__', None)
        if origin is None:
            # field is not "typing" object eg. Union, Dict, List etc.
            return

        if origin is Union:
            types_ = []
            for type_ in self.type_.__args__:
                if type_ is NoneType:
                    self.allow_none = True
                else:
                    types_.append(type_)
            self.sub_fields = [self.__class__(
                type_=t,
                class_validators=class_validators,
                default=self.default,
                required=self.required,
                allow_none=self.allow_none,
                name=f'{self.name}_{type_display(t)}',
                model_config=self.model_config,
            ) for t in types_]
            self.multipart = True
        elif issubclass(origin, List):
            self.type_ = self.type_.__args__[0]
            self.shape = Shape.LIST
        elif issubclass(origin, Set):
            self.type_ = self.type_.__args__[0]
            self.shape = Shape.SET
        else:
            assert issubclass(origin, Mapping)
            self.key_type_ = self.type_.__args__[0]
            self.type_ = self.type_.__args__[1]
            self.shape = Shape.MAPPING
            self.key_field = self.__class__(
                type_=self.key_type_,
                class_validators=class_validators,
                default=self.default,
                required=self.required,
                allow_none=self.allow_none,
                name=f'key_{self.name}',
                model_config=self.model_config,
            )

        if self.sub_fields is None and getattr(self.type_, '__origin__', False):
            self.multipart = True
            self.sub_fields = [self.__class__(
                type_=self.type_,
                class_validators=class_validators,
                default=self.default,
                required=self.required,
                allow_none=self.allow_none,
                name=f'_{self.name}',
                model_config=self.model_config,
            )]

    def _populate_validators(self, class_validators):
        get_validators = getattr(self.type_, 'get_validators', None)
        v_funcs = (
            class_validators.get(f'validate_{self.name}_pre'),

            *(get_validators() if get_validators else find_validators(self.type_)),

            class_validators.get(f'validate_{self.name}'),
            class_validators.get(f'validate_{self.name}_post'),
        )
        for f in v_funcs:
            if not f or (self.allow_none and f is not_none_validator):
                continue
            self.validators.append((
                _get_validator_signature(f),
                f,
            ))

    def validate(self, v, values, index=None):
        if self.allow_none and v is None:
            return None, None

        if self.shape is Shape.SINGLETON:
            return self._validate_singleton(v, values, index)
        elif self.shape is Shape.MAPPING:
            return self._validate_mapping(v, values)
        else:
            # list or set
            result, errors = self._validate_sequence(v, values)
            if not errors and self.shape is Shape.SET:
                return set(result), errors
            return result, errors

    def _validate_sequence(self, v, values):
        result, errors = [], []
        try:
            v_iter = enumerate(v)
        except TypeError as exc:
            return v, Error(exc, None, None)
        for i, v_ in v_iter:
            single_result, single_errors = self._validate_singleton(v_, values, i)
            if single_errors:
                errors.append(single_errors)
            else:
                result.append(single_result)
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_mapping(self, v, values):
        if isinstance(v, dict):
            v_iter = v
        else:
            try:
                v_iter = dict(v)
            except TypeError as exc:
                return v, Error(exc, None, None)

        result, errors = {}, []
        for k, v_ in v_iter.items():
            key_result, key_errors = self.key_field.validate(k, values, 'key')
            if key_errors:
                errors.append(key_errors)
                continue
            value_result, value_errors = self._validate_singleton(v_, values, k)
            if value_errors:
                errors.append(value_errors)
                continue
            result[key_result] = value_result
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_singleton(self, v, values, index):
        if self.multipart:
            errors = []
            for field in self.sub_fields:
                value, error = field.validate(v, values, index)
                if error:
                    errors.append(error)
                else:
                    return value, None
            return v, errors[0] if len(self.sub_fields) == 1 else errors
        else:
            for signature, validator in self.validators:
                try:
                    if signature is ValidatorSignature.JUST_VALUE:
                        v = validator(v)
                    else:
                        # ValidatorSignature.VALUE_KWARGS
                        v = validator(v, values=values, config=self.model_config, field=self)
                except (ValueError, TypeError) as exc:
                    return v, Error(exc, self.type_, index)
            return v, None

    def __repr__(self):
        return f'<Field {self}>'

    def __str__(self):
        if self.alt_alias:
            return f"{self.name} (alias '{self.alias}'): " + ', '.join(f'{k}={v!r}' for k, v in self.info.items())
        else:
            return f'{self.name}: ' + ', '.join(f'{k}={v!r}' for k, v in self.info.items())


def _get_validator_signature(validator):
    try:
        signature = inspect.signature(validator)
    except ValueError:
        # happens on builtins like float
        return ValidatorSignature.JUST_VALUE

    # bind here will raise a TypeError so:
    # 1. we can deal with it before validation begins
    # 2. (more importantly) it doesn't get confused with a TypeError when executing the validator
    try:
        if len(signature.parameters) == 1:
            signature.bind(1)
            return ValidatorSignature.JUST_VALUE
        else:
            signature.bind(1, values=2, config=3, field=4)
            return ValidatorSignature.VALUE_KWARGS
    except TypeError as e:
        raise ConfigError(f'Invalid signature for validator {validator}: {signature}, should be: '
                          f'(value) or (value, *, values, config, field)') from e


def _get_field_config(config, name):
    field_config = config.fields.get(name)
    if isinstance(field_config, str):
        field_config = {'alias': field_config}
    return field_config
