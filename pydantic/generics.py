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
from .typing import display_as_type, get_args, get_origin, typing_base
from .utils import all_identical, lenient_issubclass

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
        """Instantiates a new class from a generic class `cls` and type variables `params`.

        :param params: Tuple of types the class . Given a generic class
            `Model` with 2 type variables and a concrete model `Model[str, int]`,
            the value `(str, int)` would be passed to `params`.
        :return: New model class inheriting from `cls` with instantiated
            types described by `params`. If no parameters are given, `cls` is
            returned as is.

        """
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
        # Build map from generic typevars to passed params
        typevars_map: Dict[TypeVarType, Type[Any]] = dict(zip(cls.__parameters__, params))
        if all_identical(typevars_map.keys(), typevars_map.values()) and typevars_map:
            return cls  # if arguments are equal to parameters it's the same object

        # Recursively walk class type hints and replace generic typevars
        # with concrete types that were passed.
        type_hints = get_type_hints(cls).items()
        instance_type_hints = {k: v for k, v in type_hints if get_origin(v) is not ClassVar}
        concrete_type_hints: Dict[str, Type[Any]] = {
            k: replace_types(v, typevars_map) for k, v in instance_type_hints.items()
        }

        # Create new model with original model as parent inserting fields with
        # updated type hints.
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

        # Find any typevars that are still present in the model.
        # If none are left, the model is fully "concrete", otherwise the new
        # class is a generic class as well taking the found typevars as
        # parameters.
        new_params = tuple(
            {param: None for param in iter_contained_typevars(typevars_map.values())}
        )  # use dict as ordered set
        created_model.__concrete__ = not new_params
        if new_params:
            created_model.__parameters__ = new_params

        # Save created model in cache so we don't end up creating duplicate
        # models that should be identical.
        _generic_types_cache[(cls, params)] = created_model
        if len(params) == 1:
            _generic_types_cache[(cls, params[0])] = created_model
        return created_model

    @classmethod
    def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
        """Compute class name for child classes.

        :param params: Tuple of types the class . Given a generic class
            `Model` with 2 type variables and a concrete model `Model[str, int]`,
            the value `(str, int)` would be passed to `params`.
        :return: String representing a the new class where `params` are
            passed to `cls` as type variables.

        This method can be overridden to achieve a custom naming scheme for GenericModels.
        """
        param_names: List[str] = []
        param_names = [display_as_type(param) for param in params]
        params_component = ', '.join(param_names)
        return f'{cls.__name__}[{params_component}]'


def replace_types(type_: Any, type_map: Dict[Any, Any]) -> Any:
    """Return type with all occurances of `type_map` keys recursively replaced with their values.

    :param type_: Any type, class or generic alias
    :type_map: Mapping from `TypeVar` instance to concrete types.
    :return: New type representing the basic structure of `type_` with all
        `typevar_map` keys recursively replaced.

    >>> replace_types(Tuple[str, Union[List[str], float]], {str: int})
    Tuple[int, Union[List[int], float]]

    """
    if not type_map:
        return type_

    type_args = get_args(type_)
    origin_type = get_origin(type_)

    # Having type args is a good indicator that this is a typing module
    # class instantiation or a generic alias of some sort.
    if type_args:
        resolved_type_args = tuple(replace_types(arg, type_map) for arg in type_args)
        if all_identical(type_args, resolved_type_args):
            # If all arguments are the same, there is no need to modify the
            # type or create a new object at all
            return type_
        if origin_type is not None:
            # In python < 3.9 generic aliases don't exist so any of these like `list`,
            # `type` or `collections.abc.Callable` need to be translated.
            # See: https://www.python.org/dev/peps/pep-0585
            if isinstance(type_, typing_base) and not isinstance(origin_type, typing_base):
                origin_type = getattr(typing, type_._name)
        return origin_type[resolved_type_args]

    # We handle pydantic generic models separately as they don't have the same
    # semantics as "typing" classes or generic aliases
    if not origin_type and lenient_issubclass(type_, GenericModel) and not type_.__concrete__:
        type_args = type_.__parameters__
        resolved_type_args = tuple(replace_types(t, type_map) for t in type_args)
        if all_identical(type_args, resolved_type_args):
            return type_
        return type_[resolved_type_args]

    # Handle special case for typehints that can have lists as arguments.
    # `typing.Callable[[int, str], int]` is an example for this.
    if isinstance(type_, (List, list)):
        resolved_list = list(replace_types(element, type_map) for element in type_)
        if all_identical(type_, resolved_list):
            return type_
        return resolved_list

    # If all else fails, we try to resolve the type directly and otherwise just
    # return the input with no modifications.
    return type_map.get(type_, type_)


def check_parameters_count(cls: Type[GenericModel], parameters: Tuple[Any, ...]) -> None:
    actual = len(parameters)
    expected = len(cls.__parameters__)
    if actual != expected:
        description = 'many' if actual > expected else 'few'
        raise TypeError(f'Too {description} parameters for {cls.__name__}; actual {actual}, expected {expected}')


def iter_contained_typevars(v: Any) -> Iterator[TypeVarType]:
    """Recursively iterate through all subtypes and type args of `v` and yield any typevars that are found."""
    if isinstance(v, TypeVar):
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
