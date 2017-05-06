from collections import OrderedDict
from types import FunctionType

from .exceptions import Error, ValidationError
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
            field = Field.infer(
                name=var_name,
                value=value,
                annotation=annotations and annotations.get(var_name),
                class_validators=class_validators,
            )
            fields[var_name] = field
        namespace.update(
            config=config,
            __fields__=fields,
        )
        return super().__new__(mcs, name, bases, namespace)


class Missing(ValueError):
    pass


class Extra(ValueError):
    pass


MISSING = Missing('field required')
MISSING_ERROR = Error(MISSING, None, None, None)
EXTRA_ERROR = Error(Extra('extra fields not permitted'), None, None, None)


class BaseModel(metaclass=MetaModel):
    # populated by the metaclass, defined here to help IDEs only
    __fields__ = {}

    def __init__(self, **values):
        self.__values__ = {}
        self.__errors__ = OrderedDict()
        self._process_values(values)

    @property
    def values(self):
        return self.__values__

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
            value = values.get(name, MISSING)
            self._process_value(name, field, value)

        if not self.config.ignore_extra:
            extra = values.keys() - self.__fields__.keys()
            if extra:
                for field in sorted(extra):
                    self.__errors__[field] = EXTRA_ERROR

        if self.config.raise_exception and self.__errors__:
            raise ValidationError(self.__errors__)

    def _process_value(self, name, field, value):
        if value is MISSING:
            if self.config.validate_all or field.validate_always:
                value = field.default
            else:
                if field.required:
                    self.__errors__[name] = MISSING_ERROR
                else:
                    self.__values__[name] = field.default
                    # could skip this if the attributes equals field.default, would it be quicker?
                    setattr(self, name, field.default)
                return

        value, errors = field.validate(value, self)
        if errors:
            self.__errors__[name] = errors
        self.__values__[name] = value
        setattr(self, name, value)

    def __iter__(self):
        # so `dict(model)` works
        yield from self.__values__.items()

    def __repr__(self):
        return f'<{self}>'

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, ' '.join('{}={!r}'.format(k, v)
                                                                for k, v in self.__values__.items()))
