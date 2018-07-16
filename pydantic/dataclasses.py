from dataclasses import dataclass as dc
from .main import validate_model, create_model


def pydantic_model(cls):
    fields = {name: (field.type, field.default)
              for name, field
              in cls.__dataclass_fields__.items()}
    model = create_model('', **fields)
    return model


def dataclass(_cls=None, *, init=True, repr=True, eq=True,
              order=False, unsafe_hash=False, frozen=False):
    def wrap(cls):
        post_init_orig = getattr(cls, '__post_init__', lambda self: None)
        cls.__post_init__ = post_init_orig
        cls = dc(init=init, repr=repr, eq=eq, order=order,
                 unsafe_hash=unsafe_hash, frozen=frozen)(cls)
        model = pydantic_model(cls)

        def set_attr(self, name, value):
            super(cls, self).__setattr__(name, value)
            if getattr(self, '__initialized', False):
                validate_model(model, self.__dict__)

        def post_init(self):
            post_init_orig(self)
            validate_model(model, self.__dict__)
            if not frozen:
                self.__initialized = True

        if not frozen:
            cls.__setattr__ = set_attr

        cls.__post_init__ = post_init

        return cls

    if _cls is None:
        return wrap

    return wrap(_cls)
