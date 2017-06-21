from collections import OrderedDict
from types import FunctionType
from typing import Any, Dict, Set

from .exceptions import Error, Extra, Missing, ValidationError
from .fields import Field
from .validators import dict_validator


class BaseConfig:
    min_anystr_length = 0
    max_anystr_length = 2 ** 16
    min_number_size = -2 ** 64
    max_number_size = 2 ** 64
    validate_all = False
    ignore_extra = True
    allow_extra = False
    allow_mutation = True
    fields = {}


def inherit_config(self_config, parent_config) -> BaseConfig:
    if not self_config:
        return parent_config
    for k, v in parent_config.__dict__.items():
        if not (k.startswith('_') or hasattr(self_config, k)):
            setattr(self_config, k, v)
    return self_config


TYPE_BLACKLIST = FunctionType, property, type, classmethod, staticmethod


class MetaModel(type):
    @classmethod
    def __prepare__(mcs, *args, **kwargs):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        fields = OrderedDict()
        config = BaseConfig
        for base in reversed(bases):
            if issubclass(base, BaseModel) and base != BaseModel:
                fields.update(base.__fields__)
                config = inherit_config(base.config, config)

        annotations = namespace.get('__annotations__')
        config = inherit_config(namespace.get('Config'), config)
        class_validators = {n: f for n, f in namespace.items()
                            if n.startswith('validate_') and isinstance(f, FunctionType)}

        for var_name, value in namespace.items():
            if var_name.startswith('_') or isinstance(value, TYPE_BLACKLIST):
                continue
            fields[var_name] = Field.infer(
                name=var_name,
                value=value,
                annotation=annotations.pop(var_name, None) if annotations else None,
                class_validators=class_validators,
                config=config,
            )

        if annotations:
            for ann_name, ann_type in annotations.items():
                if ann_name.startswith('_'):
                    continue
                fields[ann_name] = Field.infer(
                    name=ann_name,
                    value=...,
                    annotation=ann_type,
                    class_validators=class_validators,
                    config=config,
                )

        new_namespace = {
            'config': config,
            '__fields__': fields,
            **{n: v for n, v in namespace.items() if n not in fields}
        }
        return super().__new__(mcs, name, bases, new_namespace)


MISSING = Missing('field required')
MISSING_ERROR = Error(MISSING, None, None)
EXTRA_ERROR = Error(Extra('extra fields not permitted'), None, None)


class BaseModel(metaclass=MetaModel):
    # populated by the metaclass, defined here to help IDEs only
    __fields__ = {}
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
        if not self.config.allow_extra and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        elif not self.config.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and does not support item assignment')
        self.__values__[name] = value

    def __getstate__(self):
        return self.__values__

    def __setstate__(self, state):
        object.__setattr__(self, '__values__', state)

    def values(self, *, include: Set[str]=None, exclude: Set[str]=set()) -> Dict[str, Any]:
        """
        Get a dict of the values processed by the model, optionally specifying which fields to include or exclude.

        This is NOT equivalent to the values() method on a dict.
        """
        return {
            k: v for k, v in self
            if k not in exclude and (not include or k in include)
        }

    @classmethod
    def construct(cls, **values):
        """
        Creates a new model and set __values__ without any validation, thus values should be trusted
        data. Chances are you don't want to use this method directly.
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
    def get_validators(cls):
        yield dict_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return cls(**value)

    def _process_values(self, input_data: dict) -> OrderedDict:  # noqa: C901
        values = OrderedDict()
        errors = OrderedDict()

        for name, field in self.__fields__.items():
            value = input_data.get(field.alias, MISSING)
            if value is MISSING:
                if self.config.validate_all or field.validate_always:
                    value = field.default
                else:
                    if field.required:
                        errors[field.alias] = MISSING_ERROR
                    else:
                        values[name] = field.default
                    continue

            values[name], errors_ = field.validate(value, values)
            if errors_:
                errors[field.alias] = errors_

        if (not self.config.ignore_extra) or self.config.allow_extra:
            extra = input_data.keys() - {f.alias for f in self.__fields__.values()}
            if extra:
                if self.config.allow_extra:
                    for field in extra:
                        values[field] = input_data[field]
                else:
                    # config.ignore_extra is False
                    for field in sorted(extra):
                        errors[field] = EXTRA_ERROR

        if errors:
            raise ValidationError(errors)
        return values

    @classmethod
    def _get_value(cls, v):
        if isinstance(v, BaseModel):
            return v.values()
        elif isinstance(v, list):
            return [cls._get_value(v_) for v_ in v]
        elif isinstance(v, dict):
            return {k_: cls._get_value(v_) for k_, v_ in v.items()}
        elif isinstance(v, set):
            return {cls._get_value(v_) for v_ in v}
        elif isinstance(v, tuple):
            return tuple(cls._get_value(v_) for v_ in v)
        else:
            return v

    def __iter__(self):
        # so `dict(model)` works
        for k, v in self.__values__.items():
            yield k, self._get_value(v)

    def __eq__(self, other):
        if isinstance(other, BaseModel):
            return self.values() == other.values()
        else:
            return self.values() == other

    def __repr__(self):
        return f'<{self}>'

    @classmethod
    def _truncate(cls, v):
        max_len = 80
        if isinstance(v, str) and len(v) > (max_len - 2):
            # 45 so quote + string + ... + quote has length 50
            return repr(v[:(max_len - 5)] + '...')
        v = repr(v)
        if len(v) > max_len:
            v = v[:max_len - 3] + '...'
        return v

    def to_string(self, pretty=False):
        divider = '\n  ' if pretty else ' '
        return '{}{}{}'.format(
            self.__class__.__name__,
            divider,
            divider.join('{}={}'.format(k, self._truncate(v)) for k, v in self.__values__.items()),
        )

    def __str__(self):
        return self.to_string()
