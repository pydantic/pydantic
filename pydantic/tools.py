from functools import lru_cache
from typing import Any, Callable, Type, TypeVar, Union

from .typing import display_as_type

__all__ = ('parse_as_type',)

NameGenerator = Callable[[Type[Any]], str]


def _generate_parsing_type_name(type_: Any) -> str:
    return f'ParsingModel[{display_as_type(type_)}]'


@lru_cache(maxsize=2048)
def _get_parsing_type(type_: Any, type_name: Union[str, NameGenerator] = None) -> Any:
    from pydantic.main import create_model

    if type_name is None:
        type_name = _generate_parsing_type_name
    if not isinstance(type_name, str):
        type_name = type_name(type_)
    return create_model(type_name, obj=(type_, ...))


T = TypeVar('T')


def parse_as_type(obj: Any, type_: Type[T], type_name: Union[str, NameGenerator] = None) -> T:
    model_type = _get_parsing_type(type_, type_name=type_name)
    return model_type(obj=obj).obj
