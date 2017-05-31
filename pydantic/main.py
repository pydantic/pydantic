from collections import OrderedDict
from types import FunctionType

from .exceptions import Error, Extra, Missing, ValidationError
from .fields import Field
from .validators import dict_validator


class BaseConfig:
    min_anystr_length = 0
    max_anystr_length = 2 ** 16
    min_number_size = -2 ** 64
    max_number_size = 2 ** 64
    raise_exception = True
    validate_all = False
    ignore_extra = True
    allow_extra = False
    fields = None


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

        config_fields = config.fields or {}
        for var_name, value in namespace.items():
            if var_name.startswith('_') or isinstance(value, TYPE_BLACKLIST):
                continue
            field_config = config_fields.get(var_name)
            if isinstance(field_config, str):
                field_config = {'alias': field_config}
            field = Field.infer(
                name=var_name,
                value=value,
                annotation=annotations and annotations.get(var_name),
                class_validators=class_validators,
                field_config=field_config,
            )
            fields[var_name] = field
        namespace.update(
            config=config,
            __fields__=fields,
        )
        return super().__new__(mcs, name, bases, namespace)


MISSING = Missing('field required')
MISSING_ERROR = Error(MISSING, None, None)
EXTRA_ERROR = Error(Extra('extra fields not permitted'), None, None)


class BaseModel(metaclass=MetaModel):
    # populated by the metaclass, defined here to help IDEs only
    __fields__ = {}

    def __init__(self, **values):
        self.__values__ = {}
        self.__errors__ = OrderedDict()
        self._process_values(values)

    def setattr(self, name, value):
        """
        alternative to setattr() which checks the field exists and updates __values__.

        This exists instead of overriding __setattr__ as that seems to cause a universal 10% slow down.
        """
        if not self.config.allow_extra and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        setattr(self, name, value)
        self.__values__[name] = value

    @property
    def values(self):
        return dict(self)

    @property
    def fields(self):
        return self.__fields__

    @property
    def errors(self):
        return self.__errors__

    @classmethod
    def get_validators(cls):
        yield dict_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return cls(**value)

    def _process_values(self, values):
        for name, field in self.__fields__.items():
            value = values.get(field.alias, MISSING)
            self._process_value(name, field.alias, field, value)

        if not self.config.ignore_extra or self.config.allow_extra:
            extra = values.keys() - {f.alias for f in self.__fields__.values()}
            if extra:
                if self.config.allow_extra:
                    for field in extra:
                        value = values[field]
                        self.__values__[field] = value
                        setattr(self, field, value)
                else:
                    # config.ignore_extra is False
                    for field in sorted(extra):
                        self.__errors__[field] = EXTRA_ERROR

        if self.config.raise_exception and self.__errors__:
            raise ValidationError(self.__errors__)

    def _process_value(self, name, alias, field, value):
        if value is MISSING:
            if self.config.validate_all or field.validate_always:
                value = field.default
            else:
                if field.required:
                    self.__errors__[alias] = MISSING_ERROR
                else:
                    self.__values__[name] = field.default
                    # could skip this if the attributes equals field.default, would it be quicker?
                    setattr(self, name, field.default)
                return

        value, errors = field.validate(value, self)
        if errors:
            self.__errors__[alias] = errors
        self.__values__[name] = value
        setattr(self, name, value)

    @classmethod
    def _get_value(cls, v):
        if isinstance(v, BaseModel):
            return v.values
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
            return self.values == other.values
        else:
            return self.values == other

    def __repr__(self):
        return f'<{self}>'

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, ' '.join('{}={!r}'.format(k, v)
                                                                for k, v in self.__values__.items()))
