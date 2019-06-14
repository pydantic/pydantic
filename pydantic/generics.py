from typing import TYPE_CHECKING, Any, Dict, NoReturn, Tuple, Type, TypeVar, Union, get_type_hints, no_type_check

from pydantic import BaseModel, create_model
from pydantic.class_validators import gather_validators

_generic_types_cache: Dict[Tuple[Type[Any], Tuple[Any, ...]], Type[Any]] = {}


class GenericModel:
    __slots__ = ()
    __parameters__ = ()

    def __new__(cls, *args: Any, **kwargs: Any) -> NoReturn:
        if cls is GenericModel:
            raise TypeError(f'Type {cls.__name__} cannot be instantiated; it can be used only as a base class')
        else:
            raise TypeError(f'Type {cls.__name__} cannot be instantiated without providing generic parameters')

    if TYPE_CHECKING:  # pragma: no cover

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            ...

    @no_type_check
    def __class_getitem__(cls, params: Union[Any, Tuple[Any, ...]]) -> Type[BaseModel]:
        # Annotated as Type[BaseModel] rather than a Union for better integration with editors that ignore no_type_check
        if not isinstance(params, tuple):
            params = (params,)
        cached = _generic_types_cache.get((cls, params))
        if cached is not None:
            return cached
        if cls is GenericModel:
            # Generate a TypeVar-parameterized subclass
            if not all(isinstance(x, TypeVar) for x in params):
                raise TypeError(f'Each parameter to {cls.__name__} must be a TypeVar')
            created_type = type('ParameterizedGenericModel', (GenericModel,), {'__parameters__': params})
            _generic_types_cache[(cls, params)] = created_type
            return created_type
        else:
            # Generate a parameterized BaseModel
            check_parameters_count(cls, params)
            typevars_map = dict(zip(cls.__parameters__, params))
            concrete_type_hints = {k: resolve_type_hint(v, typevars_map) for k, v in get_type_hints(cls).items()}

            model_name = concrete_name(cls, params)
            config = cls.Config if hasattr(cls, 'Config') else None
            validators = gather_validators(cls)
            fields = {k: (v, getattr(cls, k, ...)) for k, v in concrete_type_hints.items()}
            created_model = create_model(
                model_name=model_name, __module__=cls.__module__, __config__=config, __validators__=validators, **fields
            )
            _generic_types_cache[(cls, params)] = created_model
            return created_model


def concrete_name(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
    param_names = []
    for param in params:
        if hasattr(param, '__name__'):
            param_names.append(param.__name__)
        elif hasattr(param, '__origin__'):
            param_names.append(str(param))
        else:
            raise ValueError(f'Couldn\'t get name for {param}')
    params_component = ', '.join(param_names)
    return f'{cls.__name__}[{params_component}]'


def resolve_type_hint(type_: Any, typevars_map: Dict[Any, Any]) -> Type[Any]:
    if hasattr(type_, '__origin__'):
        new_args = tuple(resolve_type_hint(x, typevars_map) for x in type_.__args__)
        if type_.__origin__ is Union:
            return type_.__origin__[new_args]
        else:
            new_args = tuple([typevars_map[x] for x in type_.__parameters__])
            return type_[new_args]
    return typevars_map.get(type_, type_)


def check_parameters_count(cls: Type[GenericModel], parameters: Tuple[Any, ...]) -> None:
    # based on typing._check_generic
    actual = len(parameters)
    expected = len(cls.__parameters__)
    if actual != expected:
        description = 'many' if actual > expected else 'few'
        raise TypeError(f'Too {description} parameters for {cls.__name__}; actual {actual}, expected {expected}')
