"""
The main purpose is to enhance stdlib dataclasses by adding validation
We also want to keep the dataclass untouched to still support the default hashing,
equality, repr, ...
This means we **don't want to create a new dataclass that inherits from it**

To make this happen, we first attach a `BaseModel` to the dataclass
and magic methods to trigger the validation of the data.

Now the problem is: for a stdlib dataclass `Item` that now has magic attributes for pydantic
how can we have a new class `ValidatedItem` to trigger validation by default and keep `Item`
behaviour untouched!

To do this `ValidatedItem` will in fact be an instance of `PydanticDataclass`, a simple wrapper
around `Item` that acts like a proxy to trigger validation.
This wrapper will just inject an extra kwarg `__pydantic_run_validation__` for `ValidatedItem`
and not for `Item`! (Note that this can always be injected "a la mano" if needed)
"""
from functools import partial, wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type, TypeVar, Union, overload

from .class_validators import gather_all_validators
from .error_wrappers import ValidationError
from .errors import DataclassTypeError
from .fields import Field, FieldInfo, Required, Undefined
from .main import create_model, validate_model
from .utils import ClassAttribute
from .wrapper import ObjectProxy

if TYPE_CHECKING:
    from .main import BaseConfig, BaseModel  # noqa: F401
    from .typing import CallableGenerator, NoArgAnyCallable

    DataclassT = TypeVar('DataclassT', bound='Dataclass')

    class Dataclass:
        # stdlib attributes
        __dataclass_fields__: Dict[str, Any]
        __dataclass_params__: Any  # in reality `dataclasses._DataclassParams`
        __post_init__: Callable[..., None]

        # Added by pydantic
        __post_init_post_parse__: Callable[..., None]
        __pydantic_initialised__: bool
        __pydantic_model__: Type[BaseModel]
        __pydantic_validate_values__: Callable[['Dataclass'], None]
        __pydantic_has_field_info_default__: bool  # whether or not a `pydantic.Field` is used as default value

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        @classmethod
        def __get_validators__(cls: Type['Dataclass']) -> 'CallableGenerator':
            pass

        @classmethod
        def __validate__(cls: Type['DataclassT'], v: Any) -> 'DataclassT':
            pass


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
) -> Callable[[Type[Any]], 'PydanticDataclass']:
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
) -> 'PydanticDataclass':
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
    config: Optional[Type['BaseConfig']] = None,
) -> Union[Callable[[Type[Any]], 'PydanticDataclass'], 'PydanticDataclass']:
    """
    Like the python standard lib dataclasses but with type validation.

    Arguments are the same as for standard dataclasses, except for `validate_assignment`, which
    has the same meaning as `Config.validate_assignment`.
    """

    def wrap(cls: Type[Any]) -> PydanticDataclass:
        import dataclasses

        cls = dataclasses.dataclass(  # type: ignore
            cls, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen
        )
        return PydanticDataclass(cls, config)

    if _cls is None:
        return wrap

    return wrap(_cls)


class PydanticDataclass(ObjectProxy):
    def __init__(self, stdlib_dc_cls: Type['Dataclass'], config: Optional[Type['BaseConfig']]) -> None:
        add_pydantic_validation_attributes(stdlib_dc_cls, config)
        self.__wrapped__ = stdlib_dc_cls

    def __instancecheck__(self, instance: Any) -> bool:
        return isinstance(instance, self.__wrapped__)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # By default we run the validation with the wrapper but can still be overwritten
        kwargs.setdefault('__pydantic_run_validation__', True)
        return self.__wrapped__(*args, **kwargs)


def add_pydantic_validation_attributes(dc_cls: Type['Dataclass'], config: Optional[Type['BaseConfig']]) -> None:
    """
    We need to replace the right method. If no `__post_init__` has been set in the stdlib dataclass
    it won't even exist (code is generated on the fly by `dataclasses`)
    By default, we run validation after `__init__` or `__post_init__` if defined
    """
    if hasattr(dc_cls, '__post_init__'):
        init = dc_cls.__init__
        post_init = dc_cls.__post_init__

        @wraps(init)
        def new_init(self: 'Dataclass', *args: Any, __pydantic_run_validation__: bool = False, **kwargs: Any) -> None:
            self.__post_init__ = partial(  # type: ignore[assignment]
                self.__post_init__, __pydantic_run_validation__=__pydantic_run_validation__
            )
            init(self, *args, **kwargs)

        @wraps(post_init)
        def new_post_init(
            self: 'Dataclass', *args: Any, __pydantic_run_validation__: bool = False, **kwargs: Any
        ) -> None:
            post_init(self, *args, **kwargs)
            if __pydantic_run_validation__:
                self.__pydantic_validate_values__()
            if hasattr(self, '__post_init_post_parse__'):
                self.__post_init_post_parse__(*args, **kwargs)

        setattr(dc_cls, '__init__', new_init)
        setattr(dc_cls, '__post_init__', new_post_init)

    else:
        init = dc_cls.__init__

        @wraps(init)
        def new_init(self: 'Dataclass', *args: Any, __pydantic_run_validation__: bool = False, **kwargs: Any) -> None:
            init(self, *args, **kwargs)
            if __pydantic_run_validation__:
                self.__pydantic_validate_values__()
            if hasattr(self, '__post_init_post_parse__'):
                # We need to find again the initvars. To do that we use `__dataclass_fields__` instead of
                # public method `dataclasses.fields`
                import dataclasses

                # get all initvars and their default values
                initvars_and_values: Dict[str, Any] = {}
                for i, f in enumerate(self.__class__.__dataclass_fields__.values()):
                    if f._field_type is dataclasses._FIELD_INITVAR:  # type: ignore[attr-defined]
                        try:
                            # set arg value by default
                            initvars_and_values[f.name] = args[i]
                        except IndexError:
                            initvars_and_values[f.name] = f.default
                initvars_and_values.update(kwargs)

                self.__post_init_post_parse__(**initvars_and_values)

        setattr(dc_cls, '__init__', new_init)

    setattr(dc_cls, '__processed__', ClassAttribute('__processed__', True))
    setattr(dc_cls, '__pydantic_initialised__', False)
    setattr(dc_cls, '__pydantic_model__', create_pydantic_model_from_dataclass(dc_cls, config))
    setattr(dc_cls, '__pydantic_validate_values__', dataclass_validate_values)
    setattr(dc_cls, '__validate__', classmethod(_validate_dataclass))
    setattr(dc_cls, '__get_validators__', classmethod(_get_validators))

    if dc_cls.__pydantic_model__.__config__.validate_assignment and not dc_cls.__dataclass_params__.frozen:
        setattr(dc_cls, '__setattr__', dataclass_validate_assignment_setattr)


def _get_validators(cls: Type['Dataclass']) -> 'CallableGenerator':
    yield cls.__validate__


def _validate_dataclass(cls: Type['DataclassT'], v: Any) -> 'DataclassT':
    if isinstance(v, cls):
        v.__pydantic_validate_values__()
        return v
    elif isinstance(v, (list, tuple)):
        return cls(*v, __pydantic_run_validation__=True)
    elif isinstance(v, dict):
        return cls(**v, __pydantic_run_validation__=True)
    else:
        raise DataclassTypeError(class_name=cls.__name__)


def create_pydantic_model_from_dataclass(
    dc_cls: Type['Dataclass'], config: Optional[Type['BaseConfig']] = None
) -> Type['BaseModel']:
    import dataclasses

    field_definitions: Dict[str, Any] = {}
    for field in dataclasses.fields(dc_cls):
        default: Any = Undefined
        default_factory: Optional['NoArgAnyCallable'] = None
        field_info: FieldInfo

        if field.default is not dataclasses.MISSING:
            default = field.default
        # mypy issue 7020 and 708
        elif field.default_factory is not dataclasses.MISSING:  # type: ignore
            default_factory = field.default_factory  # type: ignore
        else:
            default = Required

        if isinstance(default, FieldInfo):
            field_info = default
            dc_cls.__pydantic_has_field_info_default__ = True
        else:
            field_info = Field(default=default, default_factory=default_factory, **field.metadata)

        field_definitions[field.name] = (field.type, field_info)

    validators = gather_all_validators(dc_cls)
    return create_model(
        dc_cls.__name__, __config__=config, __module__=dc_cls.__module__, __validators__=validators, **field_definitions
    )


def dataclass_validate_values(self: 'Dataclass') -> None:
    if getattr(self, '__pydantic_has_field_info_default__', False):
        # We need to remove `FieldInfo` values since they are not valid as input
        # It's ok to do that because they are obviously the default values!
        input_data = {k: v for k, v in self.__dict__.items() if not isinstance(v, FieldInfo)}
    else:
        input_data = self.__dict__
    d, _, validation_error = validate_model(self.__pydantic_model__, input_data, cls=self.__class__)
    if validation_error:
        raise validation_error
    object.__setattr__(self, '__dict__', d)
    object.__setattr__(self, '__pydantic_initialised__', True)


def dataclass_validate_assignment_setattr(self: 'Dataclass', name: str, value: Any) -> None:
    if self.__pydantic_initialised__:
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


def make_dataclass_validator(dc_cls: Type['Dataclass'], config: Type['BaseConfig']) -> 'CallableGenerator':
    """
    Create a pydantic.dataclass from a builtin dataclass to add type validation
    and yield the validators
    It retrieves the parameters of the dataclass and forwards them to the newly created dataclass
    """
    yield from _get_validators(PydanticDataclass(dc_cls, config=config))
