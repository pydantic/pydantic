import sys
import typing
from types import FrameType, ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from .class_validators import gather_all_validators
from .fields import FieldInfo, ModelField
from .main import BaseModel, create_model
from .typing import get_args, get_origin
from .utils import lenient_issubclass

_generic_types_cache: Dict[Tuple[Type[Any], Union[Any, Tuple[Any, ...]]], Type[BaseModel]] = {}
GenericModelT = TypeVar('GenericModelT', bound='GenericModel')
TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type


class GenericModel(BaseModel):
    __slots__ = ()
    __concrete__: ClassVar[bool] = False

    if TYPE_CHECKING:
        # Putting this in a TYPE_CHECKING block allows us to replace `if Generic not in cls.__bases__` with
        # `not hasattr(cls, "__parameters__")`. This means we don't need to force non-concrete subclasses of
        # `GenericModel` to also inherit from `Generic`, which would require changes to the use of `create_model` below.
        __parameters__: ClassVar[Tuple[TypeVarType, ...]]

    # Setting the return type as Type[Any] instead of Type[BaseModel] prevents PyCharm warnings
    def __class_getitem__(cls: Type[GenericModelT], params: Union[Type[Any], Tuple[Type[Any], ...]]) -> Type[Any]:
        cached = _generic_types_cache.get((cls, params))
        if cached is not None:
            return cached
        if cls.__concrete__ and Generic not in cls.__bases__:
            raise TypeError('Cannot parameterize a concrete instantiation of a generic model')
        if not isinstance(params, tuple):
            params = (params,)
        if cls is GenericModel and any(isinstance(param, TypeVar) for param in params):
            raise TypeError('Type parameters should be placed on typing.Generic, not GenericModel')
        if not hasattr(cls, '__parameters__'):
            raise TypeError(f'Type {cls.__name__} must inherit from typing.Generic before being parameterized')

        check_parameters_count(cls, params)
        typevars_map: Dict[TypeVarType, Type[Any]] = dict(zip(cls.__parameters__, params))
        if is_identity_typevars_map(typevars_map):
            return cls  # if arguments are equal to parameters it's the same object
        type_hints = get_type_hints(cls).items()
        instance_type_hints = {k: v for k, v in type_hints if get_origin(v) is not ClassVar}
        concrete_type_hints: Dict[str, Type[Any]] = {
            k: resolve_type_hint(v, typevars_map) for k, v in instance_type_hints.items()
        }

        model_name = cls.__concrete_name__(params)
        validators = gather_all_validators(cls)
        fields = _build_generic_fields(cls.__fields__, concrete_type_hints, typevars_map)
        model_module = get_caller_module_name() or cls.__module__
        created_model = cast(
            Type[GenericModel],  # casting ensures mypy is aware of the __concrete__ and __parameters__ attributes
            create_model(
                model_name,
                __module__=model_module,
                __base__=cls,
                __config__=None,
                __validators__=validators,
                **fields,
            ),
        )

        if is_call_from_module():  # create global reference and therefore allow pickling
            object_in_module = sys.modules[model_module].__dict__.setdefault(model_name, created_model)
            if object_in_module is not created_model:
                # this should not ever happen because of _generic_types_cache, but just in case
                raise TypeError(f'{model_name!r} already defined above, please consider reusing it') from NameError(
                    f'Name conflict: {model_name!r} in {model_module!r} is already used by {object_in_module!r}'
                )

        created_model.Config = cls.Config

        new_params = tuple(
            {param: None for param in iter_contained_typevars(typevars_map.values())}
        )  # use dict as ordered set
        created_model.__concrete__ = not new_params
        if new_params:
            created_model.__parameters__ = new_params

        _generic_types_cache[(cls, params)] = created_model
        if len(params) == 1:
            _generic_types_cache[(cls, params[0])] = created_model
        return created_model

    @classmethod
    def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
        """
        This method can be overridden to achieve a custom naming scheme for GenericModels
        """
        try:
            GenericAlias = typing.GenericAlias  # type: ignore
        except AttributeError:
            GenericAlias = ()  # for all python < 3.9
        param_names = [
            param.__name__ if hasattr(param, '__name__') and not isinstance(param, GenericAlias) else str(param)
            for param in params
        ]
        params_component = ', '.join(param_names)
        return f'{cls.__name__}[{params_component}]'


def is_identity_typevars_map(typevars_map: Dict[TypeVarType, Type[Any]]) -> bool:
    return bool(typevars_map) and all(k is v for k, v in typevars_map.items())


def resolve_type_hint(type_: Any, typevars_map: Dict[Any, Any]) -> Any:
    type_args = get_args(type_)
    if type_args:
        concrete_type_args = tuple(resolve_type_hint(arg, typevars_map) for arg in type_args)
        origin_type = get_origin(type_)
        if origin_type is not None:
            try:
                return origin_type[concrete_type_args]
            except TypeError:
                pass
            try:
                # finally try to get origin directly from typing module
                # in particular this can happen for python < 3.9 where the origin
                # is a builtin type, see https://www.python.org/dev/peps/pep-0585
                origin_type = getattr(typing, type_._name)
                return cast(Any, origin_type)[concrete_type_args]
            except (TypeError, AttributeError):  # pragma: no cover
                pass
        # this should not be reached
        raise TypeError(f'Could not resolve type origin: {type_}')  # pragma: no cover

    if not get_origin(type_) and lenient_issubclass(type_, GenericModel) and not type_.__concrete__:
        return type_[tuple(resolve_type_hint(t, typevars_map) for t in type_.__parameters__)]
    if isinstance(type_, (List, list)):
        # handle special case for typehints that can have lists as arguments
        return list(resolve_type_hint(element, typevars_map) for element in type_)
    return typevars_map.get(type_, type_)


def check_parameters_count(cls: Type[GenericModel], parameters: Tuple[Any, ...]) -> None:
    actual = len(parameters)
    expected = len(cls.__parameters__)
    if actual != expected:
        description = 'many' if actual > expected else 'few'
        raise TypeError(f'Too {description} parameters for {cls.__name__}; actual {actual}, expected {expected}')


def iter_contained_typevars(v: Any) -> Iterator[TypeVarType]:
    if isinstance(v, cast(type, TypeVar)):  # mypy < 0.790 needs this cast
        yield v
    elif hasattr(v, '__parameters__') and not get_origin(v) and lenient_issubclass(v, GenericModel):
        yield from v.__parameters__
    elif isinstance(v, Iterable):
        for var in v:
            yield from iter_contained_typevars(var)
    else:
        args = get_args(v)
        for arg in args:
            yield from iter_contained_typevars(arg)


def _build_generic_fields(
    raw_fields: Dict[str, ModelField],
    concrete_type_hints: Dict[str, Type[Any]],
    typevars_map: Dict[TypeVarType, Type[Any]],
) -> Dict[str, Tuple[Type[Any], FieldInfo]]:
    return {
        k: (_parameterize_generic_field(v, typevars_map), raw_fields[k].field_info)
        for k, v in concrete_type_hints.items()
        if k in raw_fields
    }


def _parameterize_generic_field(field_type: Type[Any], typevars_map: Dict[TypeVarType, Type[Any]]) -> Type[Any]:
    try:
        is_model = isinstance(field_type, GenericModel) and not field_type.__concrete__
    except TypeError:
        is_model = False
    if is_model:
        parameters = tuple(typevars_map.get(param, param) for param in field_type.__parameters__)
        field_type = field_type[parameters]
    return field_type


def get_caller_module_name() -> Optional[str]:
    """
    Used inside a function to get its caller module name

    Will only work against non-compiled code, therefore used only in pydantic.generics
    """
    import inspect

    try:
        previous_caller_frame = inspect.stack()[2].frame
    except IndexError as e:
        raise RuntimeError('This function must be used inside another function') from e

    getmodule = cast(Callable[[FrameType, str], Optional[ModuleType]], inspect.getmodule)
    previous_caller_module = getmodule(previous_caller_frame, previous_caller_frame.f_code.co_filename)
    return previous_caller_module.__name__ if previous_caller_module is not None else None


def is_call_from_module() -> bool:
    """
    Used inside a function to check whether it was called globally

    Will only work against non-compiled code, therefore used only in pydantic.generics
    """
    import inspect

    try:
        previous_caller_frame = inspect.stack()[2].frame
    except IndexError as e:
        raise RuntimeError('This function must be used inside another function') from e
    return previous_caller_frame.f_locals is previous_caller_frame.f_globals
