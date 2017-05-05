import inspect
from collections import OrderedDict
from enum import IntEnum
from typing import Any, List, Type, Union  # noqa

from .exceptions import ConfigError
from .validators import NoneType, find_validator, not_none_validator

NO_RESULT = object()


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_KWARGS = 2


def type_str(type_: type):
    try:
        return type_.__name__
    except AttributeError:
        # happens with unions
        return str(type_)


class Field:
    __slots__ = ('type_', 'validator_routes', 'default', 'required', 'name', 'description',
                 'info', 'validate_always', 'allow_none')

    def __init__(
            self, *,
            type_: Type,
            default: Any=None,
            required: bool=False,
            name: str=None,
            description: str=None):

        if default and required:
            raise ConfigError("It doesn't make sense to have `default` set and `required=True`.")

        self.type_: type = type_
        self.validate_always: bool = getattr(self.type_, 'validate_always', False)
        self.validator_routes: List[ValidatorRoute] = []
        self.default: Any = default
        self.required: bool = required
        self.name: str = name
        self.description: str = description
        self.allow_none: bool = False

    def prepare(self, name, class_validators):
        self.name = self.name or name
        if self.default and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise ConfigError(f'unable to infer type for attribute "{self.name}"')

        self._populate_validator_routes(class_validators)
        validators = {
            type_str(r.type_): [v[1].__qualname__ for v in r.validators] for r in self.validator_routes
        }
        if len(validators) == 1:
            validators = list(validators.values())[0]
        self.info = OrderedDict([
            ('type', type_str(self.type_)),
            ('default', self.default),
            ('required', self.required),
            ('validators', validators)
        ])
        if self.required:
            self.info.pop('default')
        if self.description:
            self.info['description'] = self.description

    def _populate_validator_routes(self, class_validators):
        override_validator = class_validators.get(f'validate_{self.name}_override')
        if override_validator:
            self.validator_routes = [ValidatorRoute(self.type_, override_validator)]
        else:
            if getattr(self.type_, '__origin__', None) is Union:
                types = self.type_.__args__
            else:
                types = [self.type_]

            for type_ in types:
                if type_ is NoneType:
                    self.allow_none = True
                else:
                    self.validator_routes.append(ValidatorRoute(type_))

        for route in self.validator_routes:
            route.prepend(class_validators.get(f'validate_{self.name}_pre'))
            route.append(class_validators.get(f'validate_{self.name}'))
            route.append(class_validators.get(f'validate_{self.name}_post'))
            route.freeze(none_route=self.allow_none)

    def validate(self, v, model):
        if self.allow_none and v is None:
            return None, None

        errors = []
        result = NO_RESULT
        for route in self.validator_routes:
            value, error, validator = route.validate(v, model, self)
            if error:
                errors.append((error, validator, route.type_))
            elif isinstance(v, route.type_):
                # exact match: return immediately
                return value, None
            else:
                result = value
        if result != NO_RESULT:
            return result, None
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
    __slots__ = 'type_', 'validators', '_frozen', '_none_route'

    def __init__(self, type_, *validators):
        self.type_ = type_
        self.validators = list(validators or self._find_validator())
        self._frozen = False
        self._none_route = None

    def prepend(self, validator):
        assert not self._frozen
        self.validators.insert(0, validator)

    def append(self, validator):
        assert not self._frozen
        self.validators.append(validator)

    def freeze(self, none_route):
        assert not self._frozen
        self._none_route = none_route
        self._frozen = True
        tmp_validators = []
        for validator in self.validators:
            if not validator:
                continue
            if none_route and validator is not_none_validator:
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
