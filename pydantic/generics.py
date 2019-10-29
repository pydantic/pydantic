from typing import Any, ClassVar, Dict, Generic, Tuple, Type, TypeVar, Union, get_type_hints

from .class_validators import gather_all_validators
from .main import BaseModel, create_model

_generic_types_cache: Dict[Tuple[Type[Any], Union[Any, Tuple[Any, ...]]], Type[BaseModel]] = {}
GenericModelT = TypeVar('GenericModelT', bound='GenericModel')


class GenericModel(BaseModel):
    __slots__ = ()
    __concrete__: ClassVar[bool] = False

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls.__concrete__:
            return super().__new__(cls)
        else:
            raise TypeError(f'Type {cls.__name__} cannot be used without generic parameters, e.g. {cls.__name__}[T]')

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
            raise TypeError(f'Type parameters should be placed on typing.Generic, not GenericModel')
        if Generic not in cls.__bases__:
            raise TypeError(f'Type {cls.__name__} must inherit from typing.Generic before being parameterized')

        check_parameters_count(cls, params)
        typevars_map: Dict[Any, Any] = dict(zip(cls.__parameters__, params))  # type: ignore
        type_hints = get_type_hints(cls).items()
        instance_type_hints = {k: v for k, v in type_hints if getattr(v, '__origin__', None) is not ClassVar}
        concrete_type_hints: Dict[str, Type[Any]] = {
            k: resolve_type_hint(v, typevars_map) for k, v in instance_type_hints.items()
        }

        model_name = cls.__concrete_name__(params)
        validators = gather_all_validators(cls)
        fields: Dict[str, Tuple[Type[Any], Any]] = {
            k: (v, cls.__fields__[k].field_info) for k, v in concrete_type_hints.items() if k in cls.__fields__
        }
        created_model = create_model(
            model_name=model_name,
            __module__=cls.__module__,
            __base__=cls,
            __config__=None,
            __validators__=validators,
            **fields,
        )
        created_model.Config = cls.Config
        created_model.__concrete__ = True  # type: ignore
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
    expected = len(cls.__parameters__)  # type: ignore
    if actual != expected:
        description = 'many' if actual > expected else 'few'
        raise TypeError(f'Too {description} parameters for {cls.__name__}; actual {actual}, expected {expected}')
