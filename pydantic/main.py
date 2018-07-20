import json
import warnings
from abc import ABCMeta
from copy import deepcopy
from functools import partial
from itertools import chain
from pathlib import Path
from types import FunctionType
from typing import Any, Callable, Dict, Set, Type, Union

from .error_wrappers import ErrorWrapper, ValidationError
from .errors import ConfigError, ExtraError, MissingError
from .fields import Field, Validator
from .parse import Protocol, load_file, load_str_bytes
from .types import StrBytes
from .utils import clean_docstring, truncate
from .validators import dict_validator


class BaseConfig:
    title = None
    anystr_strip_whitespace = False
    min_anystr_length = 0
    max_anystr_length = 2 ** 16
    validate_all = False
    ignore_extra = True
    allow_extra = False
    allow_mutation = True
    allow_population_by_alias = False
    use_enum_values = False
    fields = {}
    validate_assignment = False
    error_msg_templates: Dict[str, str] = {}
    arbitrary_types_allowed = False

    @classmethod
    def get_field_schema(cls, name):
        field_config = cls.fields.get(name) or {}
        if isinstance(field_config, str):
            field_config = {'alias': field_config}
        return field_config


def inherit_config(self_config: Type[BaseConfig], parent_config: Type[BaseConfig]) -> Type[BaseConfig]:
    if not self_config:
        base_classes = parent_config,
    elif self_config == parent_config:
        base_classes = self_config,
    else:
        base_classes = self_config, parent_config
    return type('Config', base_classes, {})


TYPE_BLACKLIST = FunctionType, property, type, classmethod, staticmethod


class ValidatorGroup:
    def __init__(self, validators):
        self.validators = validators
        self.used_validators = {'*'}

    def get_validators(self, name):
        self.used_validators.add(name)
        specific_validators = self.validators.get(name)
        wildcard_validators = self.validators.get('*')
        if specific_validators or wildcard_validators:
            return (specific_validators or []) + (wildcard_validators or [])

    def check_for_unused(self):
        unused_validators = set(chain(*[(v.func.__name__ for v in self.validators[f] if v.check_fields)
                                        for f in (self.validators.keys() - self.used_validators)]))
        if unused_validators:
            fn = ', '.join(unused_validators)
            raise ConfigError(f"Validators defined with incorrect fields: {fn} "
                              f"(use check_fields=False if you're inheriting from the model and intended this)")


def _extract_validators(namespace):
    validators = {}
    for var_name, value in namespace.items():
        validator_config = getattr(value, '__validator_config', None)
        if validator_config:
            fields, v = validator_config
            for field in fields:
                if field in validators:
                    validators[field].append(v)
                else:
                    validators[field] = [v]
    return validators


class MetaModel(ABCMeta):
    def __new__(mcs, name, bases, namespace):
        fields: Dict[name, Field] = {}
        config = BaseConfig
        for base in reversed(bases):
            if issubclass(base, BaseModel) and base != BaseModel:
                fields.update(base.__fields__)
                config = inherit_config(base.__config__, config)

        config = inherit_config(namespace.get('Config'), config)
        vg = ValidatorGroup(_extract_validators(namespace))

        for f in fields.values():
            f.set_config(config)
            extra_validators = vg.get_validators(f.name)
            if extra_validators:
                f.class_validators += extra_validators
                # re-run prepare to add extra validators
                f.prepare()

        annotations = namespace.get('__annotations__', {})
        # annotation only fields need to come first in fields
        for ann_name, ann_type in annotations.items():
            if not ann_name.startswith('_') and ann_name not in namespace:
                fields[ann_name] = Field.infer(
                    name=ann_name,
                    value=...,
                    annotation=ann_type,
                    class_validators=vg.get_validators(ann_name),
                    config=config,
                )

        for var_name, value in namespace.items():
            if not var_name.startswith('_') and not isinstance(value, TYPE_BLACKLIST):
                fields[var_name] = Field.infer(
                    name=var_name,
                    value=value,
                    annotation=annotations.get(var_name),
                    class_validators=vg.get_validators(var_name),
                    config=config,
                )

        vg.check_for_unused()
        new_namespace = {
            '__config__': config,
            '__fields__': fields,
            '__validators__': vg.validators,
            '_schema_cache': {},
            **{n: v for n, v in namespace.items() if n not in fields}
        }
        return super().__new__(mcs, name, bases, new_namespace)


_missing = object()


class BaseModel(metaclass=MetaModel):
    # populated by the metaclass, defined here to help IDEs only
    __fields__ = {}
    __validators__ = {}

    Config = BaseConfig
    __slots__ = '__values__',

    def __init__(self, **data):
        self.__setstate__(self._process_values(data))

    def __getattr__(self, name):
        try:
            return self.__values__[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if not self.__config__.allow_extra and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        elif not self.__config__.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and does not support item assignment')
        elif self.__config__.validate_assignment:
            value_, error_ = self.fields[name].validate(value, self.dict(exclude={name}), loc=name)
            if error_:
                raise ValidationError([error_])
            else:
                self.__values__[name] = value_
        else:
            self.__values__[name] = value

    def __getstate__(self):
        return self.__values__

    def __setstate__(self, state):
        object.__setattr__(self, '__values__', state)

    def dict(self, *, include: Set[str]=None, exclude: Set[str]=set(), by_alias: bool = False) -> Dict[str, Any]:
        """
        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
        """
        get_key = self._get_key_factory(by_alias)
        get_key = partial(get_key, self.fields)

        return {
            get_key(k): v
            for k, v in self._iter(by_alias=by_alias)
            if k not in exclude and (not include or k in include)
        }

    def _get_key_factory(self, by_alias: bool) -> Callable:
        if by_alias:
            return lambda fields, key: fields[key].alias

        return lambda _, key: key

    def json(self, *, include: Set[str]=None, exclude: Set[str]=set(), by_alias: bool = False, **dumps_kwargs) -> str:
        """
        Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`. Other arguments
        as per `json.dumps()`.
        """
        from .json import pydantic_encoder
        return json.dumps(
            self.dict(include=include, exclude=exclude, by_alias=by_alias),
            default=pydantic_encoder, **dumps_kwargs
        )

    @classmethod
    def parse_obj(cls, obj):
        if not isinstance(obj, dict):
            exc = TypeError(f'{cls.__name__} expected dict not {type(obj).__name__}')
            raise ValidationError([ErrorWrapper(exc, loc='__obj__')])
        return cls(**obj)

    @classmethod
    def parse_raw(cls, b: StrBytes, *,
                  content_type: str=None,
                  encoding: str='utf8',
                  proto: Protocol=None,
                  allow_pickle: bool=False):
        try:
            obj = load_str_bytes(b, proto=proto, content_type=content_type, encoding=encoding,
                                 allow_pickle=allow_pickle)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            raise ValidationError([ErrorWrapper(e, loc='__obj__')])
        return cls.parse_obj(obj)

    @classmethod
    def parse_file(cls, path: Union[str, Path], *,
                   content_type: str=None,
                   encoding: str='utf8',
                   proto: Protocol=None,
                   allow_pickle: bool=False):
        obj = load_file(path, proto=proto, content_type=content_type, encoding=encoding, allow_pickle=allow_pickle)
        return cls.parse_obj(obj)

    @classmethod
    def construct(cls, **values):
        """
        Creates a new model and set __values__ without any validation, thus values should already be trusted.
        Chances are you don't want to use this method directly.
        """
        m = cls.__new__(cls)
        m.__setstate__(values)
        return m

    def copy(self, *, include: Set[str]=None, exclude: Set[str]=None, update: Dict[str, Any]=None):
        """
        Duplicate a model, optionally choose which fields to include, exclude and change.

        :param include: fields to include in new model
        :param exclude: fields to exclude from new model, as with values this takes precedence over include
        :param update: values to change/add in the new model. Note: the data is not validated before creating
            the new model: you should trust this data
        :return: new model instance
        """
        if include is None and exclude is None and update is None:
            # skip constructing values if no arguments are passed
            v = self.__values__
        else:
            exclude = exclude or set()
            v = {
                **{k: v for k, v in self.__values__.items() if k not in exclude and (not include or k in include)},
                **(update or {})
            }
        return self.__class__.construct(**v)

    @property
    def fields(self):
        return self.__fields__

    @classmethod
    def type_schema(cls, by_alias):
        return {
            'type': 'object',
            'properties': (
                {f.alias: f.schema(by_alias) for f in cls.__fields__.values()}
                if by_alias else
                {k: f.schema(by_alias) for k, f in cls.__fields__.items()}
            )
        }

    @classmethod
    def schema(cls, by_alias=True) -> Dict[str, Any]:
        cached = cls._schema_cache.get(by_alias)
        if cached is not None:
            return cached
        s = {'title': cls.__config__.title or cls.__name__}
        if cls.__doc__:
            s['description'] = clean_docstring(cls.__doc__)

        s.update(cls.type_schema(by_alias))
        cls._schema_cache[by_alias] = s
        return s

    @classmethod
    def schema_json(cls, *, by_alias=True, **dumps_kwargs) -> str:
        from .json import pydantic_encoder
        return json.dumps(cls.schema(by_alias=by_alias), default=pydantic_encoder, **dumps_kwargs)

    @classmethod
    def get_validators(cls):
        yield dict_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return cls(**value)

    def _process_values(self, input_data: dict) -> Dict[str, Any]:  # noqa: C901 (ignore complexity)
        return validate_model(self, input_data)

    @classmethod
    def _get_value(cls, v, by_alias=False):
        if isinstance(v, BaseModel):
            return v.dict(by_alias=by_alias)
        elif isinstance(v, list):
            return [cls._get_value(v_, by_alias=by_alias) for v_ in v]
        elif isinstance(v, dict):
            return {k_: cls._get_value(v_, by_alias=by_alias) for k_, v_ in v.items()}
        elif isinstance(v, set):
            return {cls._get_value(v_, by_alias=by_alias) for v_ in v}
        elif isinstance(v, tuple):
            return tuple(cls._get_value(v_, by_alias=by_alias) for v_ in v)
        else:
            return v

    def __iter__(self):
        """
        so `dict(model)` works
        """
        yield from self._iter()

    def _iter(self, by_alias=False):
        for k, v in self.__values__.items():
            yield k, self._get_value(v, by_alias=by_alias)

    def __eq__(self, other):
        if isinstance(other, BaseModel):
            return self.dict() == other.dict()
        else:
            return self.dict() == other

    def __repr__(self):
        return f'<{self}>'

    def to_string(self, pretty=False):
        divider = '\n  ' if pretty else ' '
        return '{}{}{}'.format(
            self.__class__.__name__,
            divider,
            divider.join('{}={}'.format(k, truncate(v)) for k, v in self.__values__.items()),
        )

    def __str__(self):
        return self.to_string()


def create_model(
        model_name: str, *,
        __config__: Type[BaseConfig]=None,
        __base__: Type[BaseModel]=None,
        **field_definitions):
    """
    Dynamically create a model.
    :param model_name: name of the created model
    :param __config__: config class to use for the new model
    :param __base__: base class for the new model to inherit from
    :param **field_definitions: fields of the model (or extra fields if a base is supplied) in the format
        `<name>=(<type>, <default default>)` or `<name>=<default value> eg. `foobar=(str, ...)` or `foobar=123`
    """
    if __base__:
        fields = deepcopy(__base__.__fields__)
        validators = __base__.__validators__
        if __config__ is not None:
            raise ConfigError('to avoid confusion __config__ and __base__ cannot be used together')
    else:
        __base__ = BaseModel
        fields = {}
        validators = {}

    config = __config__ or BaseConfig
    vg = ValidatorGroup(validators)

    for f_name, f_def in field_definitions.items():
        if isinstance(f_def, tuple):
            try:
                f_annotation, f_value = f_def
            except ValueError as e:
                raise ConfigError(f'field definitions should either be a tuple of (<type>, <default>) or just a '
                                  f'default value, unfortunately this means tuples as '
                                  f'default values are not allowed') from e
        else:
            f_annotation, f_value = None, f_def
        if f_name.startswith('_'):
            warnings.warn(f'fields may not start with an underscore, ignoring "{f_name}"', RuntimeWarning)
        else:
            fields[f_name] = Field.infer(
                name=f_name,
                value=f_value,
                annotation=f_annotation,
                class_validators=vg.get_validators(f_name),
                config=config,
            )

    namespace = {
        'config': config,
        '__fields__': fields,
    }
    return type(model_name, (__base__,), namespace)


_FUNCS = set()


def validator(*fields, pre: bool=False, whole: bool=False, always: bool=False, check_fields: bool=True):
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param pre: whether or not this validator should be called before the standard validators (else after)
    :param whole: for complex objects (sets, lists etc.) whether to validate individual elements or the whole object
    :param always: whether this method and other validators should be called even if the value is missing
    :param check_fields: whether to check that the fields actually exist on the model
    """
    if not fields:
        raise ConfigError('validator with no fields specified')
    elif isinstance(fields[0], FunctionType):
        raise ConfigError("validators should be used with fields and keyword arguments, not bare. "
                          "E.g. usage should be `@validator('<field_name>', ...)`")

    def dec(f):
        ref = f.__module__ + '.' + f.__qualname__
        if ref in _FUNCS:
            raise ConfigError(f'duplicate validator function "{ref}"')
        _FUNCS.add(ref)
        f_cls = classmethod(f)
        f_cls.__validator_config = fields, Validator(f, pre, whole, always, check_fields)
        return f_cls
    return dec


def validate_model(model, input_data: dict, raise_exc=True):  # noqa: C901 (ignore complexity)
    """
    validate data against a model.
    """
    values = {}
    errors = []

    for name, field in model.__fields__.items():
        value = input_data.get(field.alias, _missing)
        if value is _missing and model.__config__.allow_population_by_alias and field.alt_alias:
            value = input_data.get(field.name, _missing)

        if value is _missing:
            if model.__config__.validate_all or field.validate_always:
                value = deepcopy(field.default)
            else:
                if field.required:
                    errors.append(ErrorWrapper(MissingError(), loc=field.alias, config=model.__config__))
                else:
                    values[name] = deepcopy(field.default)
                continue

        v_, errors_ = field.validate(value, values, loc=field.alias, cls=model.__class__)
        if isinstance(errors_, ErrorWrapper):
            errors.append(errors_)
        elif isinstance(errors_, list):
            errors.extend(errors_)
        else:
            values[name] = v_

    if (not model.__config__.ignore_extra) or model.__config__.allow_extra:
        extra = input_data.keys() - {f.alias for f in model.__fields__.values()}
        if extra:
            if model.__config__.allow_extra:
                for field in extra:
                    values[field] = input_data[field]
            else:
                # config.ignore_extra is False
                for field in sorted(extra):
                    errors.append(ErrorWrapper(ExtraError(), loc=field, config=model.__config__))

    if not raise_exc:
        return values, ValidationError(errors) if errors else None

    if errors:
        raise ValidationError(errors)
    return values
