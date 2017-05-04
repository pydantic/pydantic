import json
from types import FunctionType
from collections import OrderedDict, namedtuple
from typing import Any, Dict

from pydantic.fields import Field


DEFAULT_CONFIG: Dict[str, Any] = dict(
    min_anystr_length=0,
    max_anystr_length=2**16,
    min_number_size=-2**64,
    max_number_size=2**64,
)
Config = namedtuple('Config', list(DEFAULT_CONFIG.keys()))


def get_config(config_class):
    if config_class:
        for k, v in DEFAULT_CONFIG.items():
            if not hasattr(config_class, k):
                setattr(config_class, k, v)
    else:
        config_class = Config(**DEFAULT_CONFIG)
    return config_class


class MetaModel(type):
    @classmethod
    def __prepare__(mcs, *args, **kwargs):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        fields = OrderedDict()
        base_config = None
        for base in reversed(bases):
            if issubclass(base, BaseModel) and base != BaseModel:
                fields.update(base.__fields__)
                base_config = base.config

        annotations = namespace.get('__annotations__')
        config = get_config(namespace.get('Config', base_config))
        class_validators = {n: f for n, f in namespace.items()
                            if n.startswith('validate_') and isinstance(f, FunctionType)}

        for var_name, value in namespace.items():
            if var_name.startswith('_') or isinstance(value, (property, FunctionType, type)):
                continue
            field = Field.infer(
                name=var_name,
                value=value,
                annotation=annotations.get(var_name),
                config=config,
                class_validators=class_validators,
            )
            fields[field.name] = field
        namespace.update(
            config=config,
            __fields__=fields,
        )
        return super().__new__(mcs, name, bases, namespace)


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(f'{len(self.errors)} errors validating input: {json.dumps(errors)}')


class BaseModel(metaclass=MetaModel):
    __fields__ = {}  # populated by the metaclass
    __values__ = {}

    def __init__(self, **values):
        errors = OrderedDict()
        for name, field in self.__fields__.items():
            value = values.get(name)
            if not value:
                if field.required:
                    errors[name] = {'type': 'Missing', 'msg': 'field required'}
                continue
            try:
                value = field.validate(value)
            except (ValueError, TypeError) as e:
                errors[name] = {'type': e.__class__.__name__, 'msg': str(e)}
            else:
                self.__values__[name] = value
                setattr(self, name, value)
        if errors:
            raise ValidationError(errors)

    @property
    def values(self):
        return self.__values__

    @property
    def fields(self):
        return self.__fields__

    def _get_custom_settings(self, custom_settings):
        d = {}
        for name, value in custom_settings.items():
            if not hasattr(self, name):
                raise TypeError('{} is not a valid setting name'.format(name))
            d[name] = value
        return d

    def __iter__(self):
        # so `dict(model)` works
        yield from self.__values__.items()

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, ' '.join('{}={!r}'.format(k, v)
                                                                  for k, v in self.__values__.items()))
