from collections import OrderedDict


class MetaModel(type):
    @classmethod
    def __prepare__(mcs, *args, **kwargs):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        fields = OrderedDict()
        for base in reversed(bases):
            if issubclass(base, BaseModel) and base != BaseModel:
                fields.update(base.fields)
        annotations = namespace.get('__annotations__')
        if annotations:
            print(f'class {name}')
            fields.update(annotations)
            print(fields)
        namespace.update(
            fields=fields
        )
        return super().__new__(mcs, name, bases, namespace)


class BaseModel(metaclass=MetaModel):
    def __init__(self, **custom_settings):
        """
        :param custom_settings: Custom settings to override defaults, only attributes already defined can be set.
        """
        self._dict = {
            # **self._substitute_environ(custom_settings),
            **self._get_custom_settings(custom_settings),
        }
        [setattr(self, k, v) for k, v in self._dict.items()]

    @property
    def dict(self):
        return self._dict

    def _get_custom_settings(self, custom_settings):
        d = {}
        for name, value in custom_settings.items():
            if not hasattr(self, name):
                raise TypeError('{} is not a valid setting name'.format(name))
            d[name] = value
        return d

    def __iter__(self):
        # so `dict(settings)` works
        yield from self._dict.items()

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, ' '.join('{}={!r}'.format(k, v) for k, v in self.dict.items()))
