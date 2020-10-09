from typing import TYPE_CHECKING, Any, ClassVar, Dict, Tuple, Type, Set, TypeVar, Union, cast, get_type_hints, \
    Iterable, Iterator

from .class_validators import gather_all_validators
from .fields import FieldInfo, ModelField
from .main import BaseModel, create_model
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
        if cls.__concrete__:
            raise TypeError('Cannot parameterize a concrete instantiation of a generic model')
        if not isinstance(params, tuple):
            params = (params,)
        if cls is GenericModel and any(isinstance(param, TypeVar) for param in params):  # type: ignore
            raise TypeError('Type parameters should be placed on typing.Generic, not GenericModel')
        if not hasattr(cls, '__parameters__'):
            raise TypeError(f'Type {cls.__name__} must inherit from typing.Generic before being parameterized')

        check_parameters_count(cls, params)
        class_parameters = _get_class_parameters(cls)
        typevars_map: Dict[TypeVarType, Type[Any]] = dict(zip(class_parameters, params))
        type_hints = get_type_hints(cls).items()
        instance_type_hints = {k: v for k, v in type_hints if getattr(v, '__origin__', None) is not ClassVar}
        concrete_type_hints: Dict[str, Type[Any]] = {
            k: resolve_type_hint(v, typevars_map) for k, v in instance_type_hints.items()
        }

        model_name = cls.__concrete_name__(params)
        validators = gather_all_validators(cls)
        fields = _build_generic_fields(cls.__fields__, concrete_type_hints, typevars_map)
        created_model = cast(
            Type[GenericModel],  # casting ensures mypy is aware of the __concrete__ and __parameters__ attributes
            create_model(
                model_name,
                __module__=cls.__module__,
                __base__=cls,
                __config__=None,
                __validators__=validators,
                **fields,
            ),
        )
        created_model.Config = cls.Config
        concrete = all(_is_concretete(v) for v in concrete_type_hints.values())
        created_model.__concrete__ = concrete
        if not concrete:
            parameters = _get_parameters_from_type_hints(concrete_type_hints.values())
            created_model.__parameters__ = parameters
        _generic_types_cache[(cls, params)] = created_model
        if len(params) == 1:
            _generic_types_cache[(cls, params[0])] = created_model
        return created_model

    @classmethod
    def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
        """
        This method can be overridden to achieve a custom naming scheme for GenericModels
        """
        param_names = [param.__name__ if hasattr(param, '__name__') else str(param) for param in params]
        params_component = ', '.join(param_names)
        return f'{cls.__name__}[{params_component}]'


def resolve_type_hint(type_: Any, typevars_map: Dict[Any, Any]) -> Type[Any]:
    if hasattr(type_, '__origin__') and getattr(type_, '__parameters__', None):
        concrete_type_args = tuple([typevars_map[x] for x in type_.__parameters__])
        return type_[concrete_type_args]
    return typevars_map.get(type_, type_)


def check_parameters_count(cls: Type[GenericModel], parameters: Tuple[Any, ...]) -> None:
    actual = len(parameters)
    expected = _count_class_parameters(cls)
    if actual != expected:
        description = 'many' if actual > expected else 'few'
        raise TypeError(f'Too {description} parameters for {cls.__name__}; actual {actual}, expected {expected}')


def _count_class_parameters(cls: Type[GenericModel]) -> int:
    parameters = _get_class_parameters(cls)
    return len(parameters)


def _get_class_parameters(cls: Type[GenericModel]) -> Tuple[Any]:
    return tuple({param: None for param in _generate_class_parameters_from_bases(cls)})


def _generate_class_parameters_from_bases(cls: Type[Any]) -> Iterator[Any]:
    if getattr(cls, '__parameters__', ()):
        # If any parameters are specified, then all parameters must be
        # specified, and we simply preserve their order
        yield from getattr(cls, '__parameters__', ())
    else:
        # All parameters are collected in the lexographic order (i.e. by first
        # appearance)
        for base in cls.__bases__:
            if hasattr(base, '__parameters__') or issubclass(base, GenericModel):
                yield from _get_class_parameters(base)


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
    if lenient_issubclass(field_type, GenericModel) and not field_type.__concrete__:
        parameters = tuple(typevars_map.get(param, param) for param in field_type.__parameters__)
        field_type = field_type[parameters]
    return field_type


def _is_concretete(v: Any) -> bool:
    if _is_typevar(v):
        return False
    else:
        parameters = getattr(v, "__parameters__", ())
        return not bool(parameters)


def _get_parameters_from_type_hints(concrete_type_hints: Iterable[Type[Any]]) -> Tuple[Type[Any], ...]:
    # get unique params while maintaining order
    unique_parameters = {k: None for k in _generate_all_parameters_from_type_hints(concrete_type_hints)}
    return tuple(unique_parameters.keys())


def _generate_all_parameters_from_type_hints(concrete_type_hints: Iterable[Type[Any]]) -> Iterator[Type[Any]]:
    for type_hint in concrete_type_hints:
        yield from _generate_parameters_from_type_hint(type_hint)


def _generate_parameters_from_type_hint(type_hint: Type[Any]) -> Iterator[Type[Any]]:
    if _is_typevar(type_hint):
        yield type_hint
    else:
        yield from getattr(type_hint, "__parameters__", ())


def _is_typevar(v: Any) -> bool:
    return isinstance(v, TypeVar)  # type: ignore
