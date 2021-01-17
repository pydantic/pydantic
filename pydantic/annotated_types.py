from typing import TYPE_CHECKING, Any, Dict, FrozenSet, NamedTuple, Type

from .fields import Required
from .main import BaseModel, create_model

if TYPE_CHECKING:

    class TypedDict(Dict[str, Any]):
        __annotations__: Dict[str, Type[Any]]
        __total__: bool
        __required_keys__: FrozenSet[str]
        __optional_keys__: FrozenSet[str]


def create_model_from_typeddict(typeddict_cls: Type['TypedDict'], **kwargs: Any) -> Type['BaseModel']:
    """
    Convert a `TypedDict` to a `BaseModel`
    Since `typing.TypedDict` in Python 3.8 does not store runtime information about optional keys,
    we warn the user if that's the case (see https://bugs.python.org/issue38834)
    """
    field_definitions: Dict[str, Any]

    # Best case scenario: with python 3.9+ or when `TypedDict` is imported from `typing_extensions`
    if hasattr(typeddict_cls, '__required_keys__'):
        field_definitions = {
            field_name: (field_type, Required if field_name in typeddict_cls.__required_keys__ else None)
            for field_name, field_type in typeddict_cls.__annotations__.items()
        }
    else:
        import warnings

        warnings.warn(
            'You should use `typing_extensions.TypedDict` instead of `typing.TypedDict` for better support! '
            'Without it, there is no way to differentiate required and optional fields when subclassed. '
            'Fields will therefore be considered all required or all optional depending on class totality.',
            UserWarning,
        )
        default_value = Required if typeddict_cls.__total__ else None
        field_definitions = {
            field_name: (field_type, default_value) for field_name, field_type in typeddict_cls.__annotations__.items()
        }

    return create_model(f'{typeddict_cls.__name__}Model', **kwargs, **field_definitions)


def create_model_from_namedtuple(namedtuple_cls: Type['NamedTuple'], **kwargs: Any) -> Type['BaseModel']:
    """
    Convert a named tuple to a `BaseModel`
    A named tuple can be created with `typing.NamedTuple` and declared annotations
    but also with `collections.namedtuple` without any, in which case we consider the type
    of all the fields to be `Any`
    """
    named_tuple_annotations: Dict[str, Type[Any]] = getattr(
        namedtuple_cls, '__annotations__', {k: Any for k in namedtuple_cls._fields}
    )
    field_definitions: Dict[str, Any] = {
        field_name: (field_type, Required) for field_name, field_type in named_tuple_annotations.items()
    }
    return create_model(f'{namedtuple_cls.__name__}Model', **kwargs, **field_definitions)
