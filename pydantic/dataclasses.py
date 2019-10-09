from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, Optional, Type, TypeVar, Union

from .class_validators import gather_all_validators
from .error_wrappers import ValidationError
from .errors import DataclassTypeError
from .fields import Required
from .main import create_model, validate_model
from .typing import AnyType

if TYPE_CHECKING:
    from .main import BaseModel  # noqa: F401

    DataclassT = TypeVar('DataclassT', bound='DataclassType')

    class DataclassType:
        __pydantic_model__: Type[BaseModel]
        __initialised__: bool

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        @classmethod
        def __validate__(cls: Type['DataclassT'], v: Any) -> 'DataclassT':
            pass

        def __call__(self: 'DataclassT', *args: Any, **kwargs: Any) -> 'DataclassT':
            pass


def _validate_dataclass(cls: Type['DataclassT'], v: Any) -> 'DataclassT':
    if isinstance(v, cls):
        return v
    elif isinstance(v, (list, tuple)):
        return cls(*v)
    elif isinstance(v, dict):
        return cls(**v)
    else:
        raise DataclassTypeError(class_name=cls.__name__)


def _get_validators(cls: Type['DataclassT']) -> Generator[Any, None, None]:
    yield cls.__validate__


def setattr_validate_assignment(self: 'DataclassType', name: str, value: Any) -> None:
    if self.__initialised__:
        d = dict(self.__dict__)
        d.pop(name, None)
        known_field = self.__pydantic_model__.__fields__.get(name, None)
        if known_field:
            value, error_ = known_field.validate(value, d, loc=name, cls=self.__class__)
            if error_:
                raise ValidationError([error_], self.__class__)

    object.__setattr__(self, name, value)


def _process_class(
    _cls: AnyType,
    init: bool,
    repr: bool,
    eq: bool,
    order: bool,
    unsafe_hash: bool,
    frozen: bool,
    config: Optional[Type[Any]],
) -> 'DataclassType':
    import dataclasses

    post_init_original = getattr(_cls, '__post_init__', None)
    if post_init_original and post_init_original.__name__ == '_pydantic_post_init':
        post_init_original = None
    if not post_init_original:
        post_init_original = getattr(_cls, '__post_init_original__', None)

    post_init_post_parse = getattr(_cls, '__post_init_post_parse__', None)

    def _pydantic_post_init(self: 'DataclassType', *initvars: Any) -> None:
        if post_init_original is not None:
            post_init_original(self, *initvars)
        d, _, validation_error = validate_model(self.__pydantic_model__, self.__dict__, cls=self.__class__)
        if validation_error:
            raise validation_error
        object.__setattr__(self, '__dict__', d)
        object.__setattr__(self, '__initialised__', True)
        if post_init_post_parse is not None:
            post_init_post_parse(self, *initvars)

    _cls.__post_init__ = _pydantic_post_init
    cls = dataclasses._process_class(_cls, init, repr, eq, order, unsafe_hash, frozen)  # type: ignore

    fields: Dict[str, Any] = {}
    for field in dataclasses.fields(cls):

        if field.default != dataclasses.MISSING:
            field_value = field.default
        # mypy issue 7020 and 708
        elif field.default_factory != dataclasses.MISSING:  # type: ignore
            field_value = field.default_factory()  # type: ignore
        else:
            field_value = Required

        fields[field.name] = (field.type, field_value)

    validators = gather_all_validators(cls)
    cls.__pydantic_model__ = create_model(
        cls.__name__, __config__=config, __module__=_cls.__module__, __validators__=validators, **fields
    )

    cls.__initialised__ = False
    cls.__validate__ = classmethod(_validate_dataclass)
    cls.__get_validators__ = classmethod(_get_validators)
    if post_init_original:
        cls.__post_init_original__ = post_init_original

    if cls.__pydantic_model__.__config__.validate_assignment and not frozen:
        cls.__setattr__ = setattr_validate_assignment

    return cls


def dataclass(
    _cls: Optional[AnyType] = None,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
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
