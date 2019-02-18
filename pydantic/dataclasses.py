import dataclasses
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, Optional, Type, Union

from . import ValidationError, errors
from .main import create_model, validate_model
from .utils import AnyType

if TYPE_CHECKING:  # pragma: no cover
    from .main import BaseConfig, BaseModel  # noqa: F401

    class DataclassType:
        __pydantic_model__: Type[BaseModel]
        __post_init_original__: Callable[..., None]
        __initialised__: bool

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        @classmethod
        def __validate__(cls, v: Any) -> 'DataclassType':
            pass


def _pydantic_post_init(self: 'DataclassType') -> None:
    d = validate_model(self.__pydantic_model__, self.__dict__)
    object.__setattr__(self, '__dict__', d)
    object.__setattr__(self, '__initialised__', True)
    if self.__post_init_original__:
        self.__post_init_original__()


def _validate_dataclass(cls: Type['DataclassType'], v: Any) -> 'DataclassType':
    if isinstance(v, cls):
        return v
    elif isinstance(v, (list, tuple)):
        return cls(*v)
    elif isinstance(v, dict):
        return cls(**v)
    else:
        raise errors.DataclassTypeError(class_name=cls.__name__)


def _get_validators(cls: Type['DataclassType']) -> Generator[Any, None, None]:
    yield cls.__validate__


def setattr_validate_assignment(self: 'DataclassType', name: str, value: Any) -> None:
    if self.__initialised__:
        d = dict(self.__dict__)
        d.pop(name)
        value, error_ = self.__pydantic_model__.__fields__[name].validate(value, d, loc=name)
        if error_:
            raise ValidationError([error_])

    object.__setattr__(self, name, value)


def _process_class(
    _cls: AnyType,
    init: bool,
    repr: bool,
    eq: bool,
    order: bool,
    unsafe_hash: bool,
    frozen: bool,
    config: Type['BaseConfig'],
) -> 'DataclassType':
    post_init_original = getattr(_cls, '__post_init__', None)
    if post_init_original and post_init_original.__name__ == '_pydantic_post_init':
        post_init_original = None
    _cls.__post_init__ = _pydantic_post_init
    cls = dataclasses._process_class(_cls, init, repr, eq, order, unsafe_hash, frozen)  # type: ignore

    fields: Dict[str, Any] = {name: (field.type, field.default) for name, field in cls.__dataclass_fields__.items()}
    cls.__post_init_original__ = post_init_original

    cls.__pydantic_model__ = create_model(cls.__name__, __config__=config, __module__=_cls.__module__, **fields)

    cls.__initialised__ = False
    cls.__validate__ = classmethod(_validate_dataclass)
    cls.__get_validators__ = classmethod(_get_validators)

    if cls.__pydantic_model__.__config__.validate_assignment and not frozen:
        cls.__setattr__ = setattr_validate_assignment

    return cls


if TYPE_CHECKING:  # pragma: no cover
    # see https://github.com/python/mypy/issues/6239 for explanation of why we do this
    from dataclasses import dataclass
else:

    def dataclass(
        _cls: Optional[AnyType] = None,
        *,
        init: bool = True,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: Type['BaseConfig'] = None,
    ) -> Union[Callable[[AnyType], 'DataclassType'], 'DataclassType']:
        """
        Like the python standard lib dataclasses but with type validation.

        Arguments are the same as for standard dataclasses, except for validate_assignment which has the same meaning
        as Config.validate_assignment.
        """

        def wrap(cls: AnyType) -> 'DataclassType':
            return _process_class(cls, init, repr, eq, order, unsafe_hash, frozen, config)

        if _cls is None:
            return wrap

        return wrap(_cls)
