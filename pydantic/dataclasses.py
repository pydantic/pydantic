import json
import typing as tp
import dataclasses

from pydantic import ValidationError

from .json import pydantic_encoder
from .main import create_model, validate_model, BaseConfig


def post_init(self):
    d = validate_model(self.__pydantic_model__, self.__dict__)
    object.__setattr__(self, '__dict__', d)
    object.__setattr__(self, '__initialised__', True)
    if self.__post_init_original__:
        self.__post_init_original__()


def setattr_validate_assignment(self, name, value):
    if self.__initialised__:
        d = dict(self.__dict__)
        d.pop(name)
        value, error_ = self.__pydantic_model__.__fields__[name].validate(value, d, loc=name)
        if error_:
            raise ValidationError([error_])

    object.__setattr__(self, name, value)


def _process_class(_cls, init, repr, eq, order, unsafe_hash, frozen, validate_assignment):
    post_init_original = getattr(_cls, '__post_init__', None)
    _cls.__post_init__ = post_init
    cls = dataclasses._process_class(_cls, init, repr, eq, order, unsafe_hash, frozen)

    fields = {name: (field.type, field.default) for name, field in cls.__dataclass_fields__.items()}
    cls.__post_init_original__ = post_init_original

    class DCConfig(BaseConfig):
        arbitrary_types_allowed = True

    cls.__pydantic_model__ = create_model(cls.__name__, __config__=DCConfig, **fields)
    cls.__initialised__ = False
    cls._json_encoder = staticmethod(pydantic_encoder)
    cls.dict = _dict
    cls.json = _json
    if validate_assignment and not frozen:
        cls.__setattr__ = setattr_validate_assignment
    return cls


def dataclass(_cls=None, *, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False,
              validate_assignment=False):
    """
    Like the python standard lib dataclasses but with type validation.

    Arguments are the same as for standard dataclasses, except for validate_assignment which has the same meaning
    as Config.validate_assignment.
    """

    def wrap(cls):
        return _process_class(cls, init, repr, eq, order, unsafe_hash, frozen, validate_assignment)

    if _cls is None:
        return wrap

    return wrap(_cls)


def _dict(self, *, include: tp.Set[str] = None, exclude: tp.Set[str] = None) -> tp.Dict[str, tp.Any]:
    """
    Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
    """
    exclude = exclude or set()
    return {
        k: v
        for k, v in dataclasses.asdict(self).items()
        if k not in exclude and (not include or k in include)
    }


def _json(self, *, include: tp.Set[str] = None, exclude: tp.Set[str] = None, encoder=None, **dumps_kwargs) -> str:
    """
    Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

    `encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
    """
    exclude = exclude or set()
    return json.dumps(
        self.dict(include=include, exclude=exclude),
        default=encoder or self._json_encoder, **dumps_kwargs
    )
