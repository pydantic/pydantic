import dataclasses

from . import ValidationError, errors
from .main import create_model, validate_model


def _pydantic_post_init(self):
    d = validate_model(self.__pydantic_model__, self.__dict__)
    object.__setattr__(self, '__dict__', d)
    object.__setattr__(self, '__initialised__', True)
    if self.__post_init_original__:
        self.__post_init_original__()


def _validate_dataclass(cls, v):
    if isinstance(v, cls):
        return v
    elif isinstance(v, (cls, list, tuple)):
        return cls(*v)
    elif isinstance(v, dict):
        return cls(**v)
    else:
        raise errors.DataclassTypeError(class_name=cls.__name__)


def _get_validators(cls):
    yield cls.__validate__


def setattr_validate_assignment(self, name, value):
    if self.__initialised__:
        d = dict(self.__dict__)
        d.pop(name)
        value, error_ = self.__pydantic_model__.__fields__[name].validate(value, d, loc=name)
        if error_:
            raise ValidationError([error_])

    object.__setattr__(self, name, value)


def _process_class(_cls, init, repr, eq, order, unsafe_hash, frozen, config):
    post_init_original = getattr(_cls, '__post_init__', None)
    if post_init_original and post_init_original.__name__ == '_pydantic_post_init':
        post_init_original = None
    _cls.__post_init__ = _pydantic_post_init
    cls = dataclasses._process_class(_cls, init, repr, eq, order, unsafe_hash, frozen)

    fields = {name: (field.type, field.default) for name, field in cls.__dataclass_fields__.items()}
    cls.__post_init_original__ = post_init_original

    cls.__pydantic_model__ = create_model(cls.__name__, __config__=config, **fields)

    cls.__initialised__ = False
    cls.__validate__ = classmethod(_validate_dataclass)
    cls.__get_validators__ = classmethod(_get_validators)

    if cls.__pydantic_model__.__config__.validate_assignment and not frozen:
        cls.__setattr__ = setattr_validate_assignment

    return cls


def dataclass(_cls=None, *, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False, config=None):
    """
    Like the python standard lib dataclasses but with type validation.

    Arguments are the same as for standard dataclasses, except for validate_assignment which has the same meaning
    as Config.validate_assignment.
    """

    def wrap(cls):
        return _process_class(cls, init, repr, eq, order, unsafe_hash, frozen, config)

    if _cls is None:
        return wrap

    return wrap(_cls)
