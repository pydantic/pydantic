import inspect
from enum import Enum, IntEnum
from typing import Any, Callable, List, Mapping, NamedTuple, Set, Type, Union

from .error_wrappers import ErrorWrapper
from .errors import ConfigError, SequenceError
from .utils import display_as_type
from .validators import NoneType, dict_validator, find_validators, not_none_validator

Required: Any = Ellipsis


class ValidatorSignature(IntEnum):
    JUST_VALUE = 1
    VALUE_KWARGS = 2
    CLS_JUST_VALUE = 3
    CLS_VALUE_KWARGS = 4


class Shape(IntEnum):
    SINGLETON = 1
    LIST = 2
    SET = 3
    MAPPING = 4


class Validator(NamedTuple):
    func: Callable
    pre: bool
    whole: bool
    always: bool
    check_fields: bool


class Schema:
    """
    Used to provide extra information about a field in a model schema.
    """
    __slots__ = 'default', 'alias', 'title', 'choice_names', 'extra',

    def __init__(self, default, *, alias=None, title=None, choice_names=None, **extra):
        self.default = default
        self.alias = alias
        self.title = title
        self.choice_names = choice_names
        self.extra = extra


class Field:
    __slots__ = (
        'type_', 'key_type_', 'sub_fields', 'key_field', 'validators', 'whole_pre_validators', 'whole_post_validators',
        'default', 'required', 'model_config', 'name', 'alias', '_schema', 'validate_always', 'allow_none', 'shape',
        'class_validators'
    )

    def __init__(
            self, *,
            name: str,
            type_: Type,
            class_validators: List[Validator],
            default: Any,
            required: bool,
            model_config: Any,
            alias: str=None,
            allow_none: bool=False,
            schema: Schema=None):

        self.name: str = name
        self.alias: str = alias or name
        self.type_: type = type_
        self.key_type_: type = None
        self.class_validators = class_validators or []
        self.validate_always: bool = False
        self.sub_fields: List[Field] = None
        self.key_field: Field = None
        self.validators = []
        self.whole_pre_validators = None
        self.whole_post_validators = None
        self.default: Any = default
        self.required: bool = required
        self.model_config = model_config
        self.allow_none: bool = allow_none
        self.shape: Shape = Shape.SINGLETON
        self._schema: Schema = schema
        self.prepare()

    @classmethod
    def infer(cls, *, name, value, annotation, class_validators, config):
        schema_from_config = config.get_field_schema(name)
        if isinstance(value, Schema):
            schema = value
            value = schema.default
        else:
            schema = Schema(value, **schema_from_config)
        schema.alias = schema.alias or schema_from_config.get('alias')
        required = value == Required
        return cls(
            name=name,
            type_=annotation,
            alias=schema.alias,
            class_validators=class_validators,
            default=None if required else value,
            required=required,
            model_config=config,
            schema=schema,
        )

    def set_config(self, config):
        self.model_config = config
        schema_from_config = config.get_field_schema(self.name)
        if schema_from_config:
            self._schema.alias = self._schema.alias or schema_from_config.get('alias')
            self.alias = self._schema.alias

    @property
    def alt_alias(self):
        return self.name != self.alias

    def prepare(self):
        if self.default is not None and self.type_ is None:
            self.type_ = type(self.default)

        if self.type_ is None:
            raise ConfigError(f'unable to infer type for attribute "{self.name}"')

        self.validate_always: bool = (
            getattr(self.type_, 'validate_always', False) or any(v.always for v in self.class_validators)
        )

        if not self.required and not self.validate_always and self.default is None:
            self.allow_none = True

        self._populate_sub_fields()
        self._populate_validators()

    def schema(self, by_alias=True):
        s = self.type_.schema(by_alias) if hasattr(self.type_, 'schema') else {}
        s.update(
            type=s.get('type') or display_as_type(self.type_),
            title=self._schema.title or s.get('title') or self.alias.title(),
            required=self.required,
        )

        if not self.required and self.default is not None:
            s['default'] = self.default
        if issubclass(self.type_, Enum):
            choice_names = self._schema.choice_names or {}
            s['choices'] = [
                (v.value, choice_names.get(v.value) or k.title())
                for k, v in self.type_.__members__.items()
            ]
        s.update(self._schema.extra)
        return s

    def _populate_sub_fields(self):
        # typing interface is horrible, we have to do some ugly checks
        origin = _get_type_origin(self.type_)
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
                class_validators=self.class_validators,
                default=self.default,
                required=self.required,
                allow_none=self.allow_none,
                name=f'{self.name}_{display_as_type(t)}',
                model_config=self.model_config,
            ) for t in types_]
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
                class_validators=self.class_validators,
                default=self.default,
                required=self.required,
                allow_none=self.allow_none,
                name=f'key_{self.name}',
                model_config=self.model_config,
            )

        if not self.sub_fields and _get_type_origin(self.type_):
            # type_ has been refined eg. as the type of a List and sub_fields needs to be populated
            self.sub_fields = [self.__class__(
                type_=self.type_,
                class_validators=self.class_validators,
                default=self.default,
                required=self.required,
                allow_none=self.allow_none,
                name=f'_{self.name}',
                model_config=self.model_config,
            )]

    def _populate_validators(self):
        if not self.sub_fields:
            get_validators = getattr(self.type_, 'get_validators', None)
            v_funcs = (
                *tuple(v.func for v in self.class_validators if not v.whole and v.pre),
                *(get_validators() if get_validators else find_validators(self.type_,
                                                                          self.model_config.arbitrary_types_allowed)),
                *tuple(v.func for v in self.class_validators if not v.whole and not v.pre),
            )
            self.validators = self._prep_vals(v_funcs)

        if self.class_validators:
            self.whole_pre_validators = self._prep_vals(v.func for v in self.class_validators if v.whole and v.pre)
            self.whole_post_validators = self._prep_vals(v.func for v in self.class_validators if v.whole and not v.pre)

    def _prep_vals(self, v_funcs):
        v = []
        for f in v_funcs:
            if not f or (self.allow_none and f is not_none_validator):
                continue
            v.append((
                _get_validator_signature(f),
                f,
            ))
        return tuple(v)

    def validate(self, v, values, *, loc, cls=None):
        if self.allow_none and v is None:
            return None, None

        if not isinstance(loc, tuple):
            loc = (loc,)

        if self.whole_pre_validators:
            v, errors = self._apply_validators(v, values, loc, cls, self.whole_pre_validators)
            if errors:
                return v, errors

        if self.shape is Shape.SINGLETON:
            v, errors = self._validate_singleton(v, values, loc, cls)
        elif self.shape is Shape.MAPPING:
            v, errors = self._validate_mapping(v, values, loc, cls)
        else:
            # list or set
            v, errors = self._validate_sequence(v, values, loc, cls)
            if not errors and self.shape is Shape.SET:
                v = set(v)

        if not errors and self.whole_post_validators:
            v, errors = self._apply_validators(v, values, loc, cls, self.whole_post_validators)
        return v, errors

    def _validate_sequence(self, v, values, loc, cls):
        result, errors = [], []

        try:
            v_iter = enumerate(v)
        except TypeError:
            return v, ErrorWrapper(SequenceError(), loc=loc, config=self.model_config)

        for i, v_ in v_iter:
            v_loc = *loc, i
            single_result, single_errors = self._validate_singleton(v_, values, v_loc, cls)
            if single_errors:
                errors.append(single_errors)
            else:
                result.append(single_result)

        if errors:
            return v, errors
        else:
            return result, None

    def _validate_mapping(self, v, values, loc, cls):
        try:
            v_iter = dict_validator(v)
        except TypeError as exc:
            return v, ErrorWrapper(exc, loc=loc, config=self.model_config)

        result, errors = {}, []
        for k, v_ in v_iter.items():
            v_loc = *loc, '__key__'
            key_result, key_errors = self.key_field.validate(k, values, loc=v_loc, cls=cls)
            if key_errors:
                errors.append(key_errors)
                continue

            v_loc = *loc, k
            value_result, value_errors = self._validate_singleton(v_, values, v_loc, cls)
            if value_errors:
                errors.append(value_errors)
                continue

            result[key_result] = value_result
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_singleton(self, v, values, loc, cls):
        if self.sub_fields:
            errors = []
            for field in self.sub_fields:
                value, error = field.validate(v, values, loc=loc, cls=cls)
                if error:
                    errors.append(error)
                else:
                    return value, None
            return v, errors
        else:
            return self._apply_validators(v, values, loc, cls, self.validators)

    def _apply_validators(self, v, values, loc, cls, validators):
        for signature, validator in validators:
            try:
                if signature is ValidatorSignature.JUST_VALUE:
                    v = validator(v)
                elif signature is ValidatorSignature.VALUE_KWARGS:
                    v = validator(v, values=values, config=self.model_config, field=self)
                elif signature is ValidatorSignature.CLS_JUST_VALUE:
                    v = validator(cls, v)
                else:
                    # ValidatorSignature.CLS_VALUE_KWARGS
                    v = validator(cls, v, values=values, config=self.model_config, field=self)
            except (ValueError, TypeError) as exc:
                return v, ErrorWrapper(exc, loc=loc, config=self.model_config)
        return v, None

    def __repr__(self):
        return f'<Field({self})>'

    def __str__(self):
        parts = [self.name, 'type=' + display_as_type(self.type_)]

        if self.required:
            parts.append('required')
        else:
            parts.append(f'default={self.default!r}')

        if self.alt_alias:
            parts.append('alias=' + self.alias)
        return ' '.join(parts)


def _get_validator_signature(validator):
    signature = inspect.signature(validator)

    # bind here will raise a TypeError so:
    # 1. we can deal with it before validation begins
    # 2. (more importantly) it doesn't get confused with a TypeError when executing the validator
    try:
        if 'cls' in signature._parameters:
            if len(signature.parameters) == 2:
                signature.bind(object(), 1)
                return ValidatorSignature.CLS_JUST_VALUE
            else:
                signature.bind(object(), 1, values=2, config=3, field=4)
                return ValidatorSignature.CLS_VALUE_KWARGS
        else:
            if len(signature.parameters) == 1:
                signature.bind(1)
                return ValidatorSignature.JUST_VALUE
            else:
                signature.bind(1, values=2, config=3, field=4)
                return ValidatorSignature.VALUE_KWARGS
    except TypeError as e:
        raise ConfigError(f'Invalid signature for validator {validator}: {signature}, should be: '
                          f'(value) or (value, *, values, config, field) or for class validators '
                          f'(cls, value) or (cls, value, *, values, config, field)') from e


def _get_type_origin(obj):
    """
    Like obj.__class__ or type(obj) but for typing objects
    """
    return getattr(obj, '__origin__', None)
