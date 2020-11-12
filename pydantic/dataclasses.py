from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type, TypeVar, Union, overload

from .class_validators import gather_all_validators
from .error_wrappers import ValidationError
from .errors import DataclassTypeError
from .fields import Required
from .main import create_model, validate_model
from .utils import ClassAttribute

if TYPE_CHECKING:
    from .main import BaseConfig, BaseModel  # noqa: F401
    from .typing import CallableGenerator

    DataclassT = TypeVar('DataclassT', bound='Dataclass')

    class Dataclass:
        __pydantic_model__: Type[BaseModel]
        __initialised__: bool
        __post_init_original__: Optional[Callable[..., None]]
        __processed__: Optional[ClassAttribute]

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        @classmethod
        def __get_validators__(cls: Type['Dataclass']) -> 'CallableGenerator':
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
    # In nested dataclasses, v can be of type `dataclasses.dataclass`.
    # But to validate fields `cls` will be in fact a `pydantic.dataclasses.dataclass`,
    # which inherits directly from the class of `v`.
    elif is_builtin_dataclass(v) and cls.__bases__[0] is type(v):
        import dataclasses

        return cls(**dataclasses.asdict(v))
    else:
        raise DataclassTypeError(class_name=cls.__name__)


def _get_validators(cls: Type['Dataclass']) -> 'CallableGenerator':
    yield cls.__validate__


def setattr_validate_assignment(self: 'Dataclass', name: str, value: Any) -> None:
    if self.__initialised__:
        d = dict(self.__dict__)
        d.pop(name, None)
        known_field = self.__pydantic_model__.__fields__.get(name, None)
        if known_field:
            value, error_ = known_field.validate(value, d, loc=name, cls=self.__class__)
            if error_:
                raise ValidationError([error_], self.__class__)

    object.__setattr__(self, name, value)


def is_builtin_dataclass(_cls: Type[Any]) -> bool:
    """
    `dataclasses.is_dataclass` is True if one of the class parents is a `dataclass`.
    This is why we also add a class attribute `__processed__` to only consider 'direct' built-in dataclasses
    """
    import dataclasses

    return not hasattr(_cls, '__processed__') and dataclasses.is_dataclass(_cls)


def _process_class(
    _cls: Type[Any],
    init: bool,
    repr: bool,
    eq: bool,
    order: bool,
    unsafe_hash: bool,
    frozen: bool,
    config: Optional[Type[Any]],
) -> Type['Dataclass']:
    import dataclasses

    post_init_original = getattr(_cls, '__post_init__', None)
    if post_init_original and post_init_original.__name__ == '_pydantic_post_init':
        post_init_original = None
    if not post_init_original:
        post_init_original = getattr(_cls, '__post_init_original__', None)

    post_init_post_parse = getattr(_cls, '__post_init_post_parse__', None)

    def _pydantic_post_init(self: 'Dataclass', *initvars: Any) -> None:
        if post_init_original is not None:
            post_init_original(self, *initvars)
        d, _, validation_error = validate_model(self.__pydantic_model__, self.__dict__, cls=self.__class__)
        if validation_error:
            raise validation_error
        object.__setattr__(self, '__dict__', d)
        object.__setattr__(self, '__initialised__', True)
        if post_init_post_parse is not None:
            post_init_post_parse(self, *initvars)

    # If the class is already a dataclass, __post_init__ will not be called automatically
    # so no validation will be added.
    # We hence create dynamically a new dataclass:
    # ```
    # @dataclasses.dataclass
    # class NewClass(_cls):
    #   __post_init__ = _pydantic_post_init
    # ```
    # with the exact same fields as the base dataclass
    # and register it on module level to address pickle problem:
    # https://github.com/samuelcolvin/pydantic/issues/2111
    if is_builtin_dataclass(_cls):
        uniq_class_name = f'_Pydantic_{_cls.__name__}_{id(_cls)}'
        _cls = type(
            # for pretty output new class will have the name as original
            _cls.__name__,
            (_cls,),
            {
                '__annotations__': _cls.__annotations__,
                '__post_init__': _pydantic_post_init,
                # attrs for pickle to find this class
                '__module__': __name__,
                '__qualname__': uniq_class_name,
            },
        )
        globals()[uniq_class_name] = _cls
    else:
        _cls.__post_init__ = _pydantic_post_init
    cls: Type['Dataclass'] = dataclasses.dataclass(  # type: ignore
        _cls, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen
    )
    cls.__processed__ = ClassAttribute('__processed__', True)

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
    cls.__validate__ = classmethod(_validate_dataclass)  # type: ignore[assignment]
    cls.__get_validators__ = classmethod(_get_validators)  # type: ignore[assignment]
    if post_init_original:
        cls.__post_init_original__ = post_init_original

    if cls.__pydantic_model__.__config__.validate_assignment and not frozen:
        cls.__setattr__ = setattr_validate_assignment  # type: ignore[assignment]

    return cls


@overload
def dataclass(
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
) -> Callable[[Type[Any]], Type['Dataclass']]:
    ...


@overload
def dataclass(
    _cls: Type[Any],
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
) -> Type['Dataclass']:
    ...


def dataclass(
    _cls: Optional[Type[Any]] = None,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
) -> Union[Callable[[Type[Any]], Type['Dataclass']], Type['Dataclass']]:
    """
    Like the python standard lib dataclasses but with type validation.

    Arguments are the same as for standard dataclasses, except for validate_assignment which has the same meaning
    as Config.validate_assignment.
    """

    def wrap(cls: Type[Any]) -> Type['Dataclass']:
        return _process_class(cls, init, repr, eq, order, unsafe_hash, frozen, config)

    if _cls is None:
        return wrap

    return wrap(_cls)


def make_dataclass_validator(_cls: Type[Any], config: Type['BaseConfig']) -> 'CallableGenerator':
    """
    Create a pydantic.dataclass from a builtin dataclass to add type validation
    and yield the validators
    It retrieves the parameters of the dataclass and forwards them to the newly created dataclass
    """
    dataclass_params = _cls.__dataclass_params__
    stdlib_dataclass_parameters = {param: getattr(dataclass_params, param) for param in dataclass_params.__slots__}
    cls = dataclass(_cls, config=config, **stdlib_dataclass_parameters)
    yield from _get_validators(cls)
