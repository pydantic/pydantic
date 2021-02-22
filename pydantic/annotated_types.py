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
    Create a `BaseModel` based on the fields of a `TypedDict`.
    Since `typing.TypedDict` in Python 3.8 does not store runtime information about optional keys,
    we raise an error if this happens (see https://bugs.python.org/issue38834).
    """
    field_definitions: Dict[str, Any]

    # Best case scenario: with python 3.9+ or when `TypedDict` is imported from `typing_extensions`
    if not hasattr(typeddict_cls, '__required_keys__'):
        raise TypeError(
            'You should use `typing_extensions.TypedDict` instead of `typing.TypedDict`. '
            'Without it, there is no way to differentiate required and optional fields when subclassed.'
        )

    field_definitions = {
        field_name: (field_type, Required if field_name in typeddict_cls.__required_keys__ else None)
        for field_name, field_type in typeddict_cls.__annotations__.items()
    }

    return create_model(typeddict_cls.__name__, **kwargs, **field_definitions)


def create_model_from_namedtuple(namedtuple_cls: Type['NamedTuple'], **kwargs: Any) -> Type['BaseModel']:
    """
    Create a `BaseModel` based on the fields of a named tuple.
    A named tuple can be created with `typing.NamedTuple` and declared annotations
    but also with `collections.namedtuple`, in this case we consider all fields
    to have type `Any`.
    """
    namedtuple_annotations: Dict[str, Type[Any]] = getattr(
        namedtuple_cls, '__annotations__', {k: Any for k in namedtuple_cls._fields}
    )
    field_definitions: Dict[str, Any] = {
        field_name: (field_type, Required) for field_name, field_type in namedtuple_annotations.items()
    }
    return create_model(namedtuple_cls.__name__, **kwargs, **field_definitions)
