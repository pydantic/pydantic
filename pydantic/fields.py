import inspect
from collections import OrderedDict
from enum import IntEnum
from typing import Any, List, Sequence, Type, Union  # noqa

from .exceptions import ConfigError, Error, type_json
from .validators import NoneType, find_validator, not_none_validator


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_KWARGS = 2


class Shape(IntEnum):
    SINGLETON = 1
    SEQUENCE = 2
    MAPPING = 3


class Field:
    __slots__ = ('type_', 'validator_tracks', 'track_count', 'default', 'required', 'name', 'description',
                 'info', 'validate_always', 'allow_none', 'shape')

    def __init__(
            self, *,
            type_: Type,
            default: Any=None,
            required: bool=False,
            name: str=None,
            description: str=None):

        self.type_: type = type_
        self.validate_always: bool = getattr(self.type_, 'validate_always', False)
        self.validator_tracks: List[ValidatorRoute] = []
        self.default: Any = default
        self.required: bool = required
        self.name: str = name
        self.description: str = description
        self.allow_none: bool = False
        self.shape: Shape = Shape.SINGLETON

    def prepare(self, name, class_validators):
        self.name = self.name or name
        if self.default and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise ConfigError(f'unable to infer type for attribute "{self.name}"')

        # typing interface is horrible, we have to do some ugly checks
        origin = getattr(self.type_, '__origin__', None)
        if origin not in (None, Union):
            if issubclass(origin, Sequence):
                self.type_ = self.type_.__args__[0]
                self.shape = Shape.SEQUENCE
            # TODO mapping

        self._populate_validator_tracks(class_validators)
        validators = {
            type_json(r.type_): [v[1].__qualname__ for v in r.validators] for r in self.validator_tracks
        }
        if len(validators) == 1:
            validators = list(validators.values())[0]
        self.info = OrderedDict([
            ('type', type_json(self.type_)),
            ('default', self.default),
            ('required', self.required),
            ('validators', validators)
        ])
        if self.required:
            self.info.pop('default')
        if self.description:
            self.info['description'] = self.description

    def _populate_validator_tracks(self, class_validators):
        override_validator = class_validators.get(f'validate_{self.name}_override')
        if override_validator:
            self.validator_tracks = [ValidatorRoute(self.type_, override_validator)]
        else:
            if getattr(self.type_, '__origin__', None) is Union:
                types = self.type_.__args__
            else:
                types = [self.type_]

            for type_ in types:
                if type_ is NoneType:
                    self.allow_none = True
                else:
                    self.validator_tracks.append(ValidatorRoute(type_))

        for track in self.validator_tracks:
            track.prepend(class_validators.get(f'validate_{self.name}_pre'))
            track.append(class_validators.get(f'validate_{self.name}'))
            track.append(class_validators.get(f'validate_{self.name}_post'))
            track.freeze(none_track=self.allow_none)

    def validate(self, v, model):
        if self.allow_none and v is None:
            return None, None

        if self.shape == Shape.SINGLETON:
            return self._validate_singleton(v, model)
        elif self.shape == Shape.SEQUENCE:
            result, errors = [], []
            try:
                v_iter = enumerate(v)
            except TypeError as exc:
                return v, Error(exc, iter, None, None)
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
        else:
            # mapping
            raise NotImplemented('TODO')

    def _validate_singleton(self, v, model, index=None):
        errors = []
        result = ...
        for track in self.validator_tracks:
            value, exc, validator = track.validate(v, model, self)
            if exc:
                errors.append(Error(exc, validator, track.type_, index))
            elif isinstance(v, track.type_):
                # exact match: return immediately
                return value, None
            else:
                result = value
        if result is not ...:
            return result, None
        elif len(self.validator_tracks) == 1:
            return v, errors[0]
        else:
            return v, errors

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


class ValidatorRoute:
    __slots__ = 'type_', 'validators', '_none_track'

    def __init__(self, type_, *validators):
        self.type_ = type_
        self.validators = list(validators or self._find_validator())
        self._none_track = None

    def prepend(self, validator):
        self.validators.insert(0, validator)

    def append(self, validator):
        self.validators.append(validator)

    def freeze(self, none_track):
        self._none_track = none_track
        tmp_validators = []
        for validator in self.validators:
            if not validator:
                continue
            if none_track and validator is not_none_validator:
                continue
            signature = self._get_validator_signature(validator)
            tmp_validators.append((signature, validator))

        self.validators = tuple(tmp_validators)

    def validate(self, v, model, field):
        for signature, validator in self.validators:
            try:
                if signature == ValidatorSignature.JUST_VALUE:
                    v = validator(v)
                else:
                    v = validator(v, model=model, field=field)
            except (ValueError, TypeError, ImportError) as e:
                return v, e, validator
        return v, None, None

    def _find_validator(self):
        get_validators = getattr(self.type_, 'get_validators', None)
        if get_validators:
            return list(get_validators())
        return find_validator(self.type_)

    @staticmethod
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
            if len(signature.parameters) == 1:
                signature.bind(1)
                return ValidatorSignature.JUST_VALUE
            else:
                signature.bind(1, model=2, field=3)
                return ValidatorSignature.VALUE_KWARGS
        except TypeError as e:
            raise ConfigError(f'Invalid signature for validator {validator}: {signature}, should be: '
                              f'(value) or (value, *, model, field)') from e
