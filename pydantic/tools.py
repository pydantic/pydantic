from functools import lru_cache
from typing import Any, Type, TypeVar

__all__ = ('parse_as_type',)


@lru_cache(maxsize=None)
def _get_parsing_type(type_: Any, source: str) -> Any:
    from pydantic.main import create_model

    type_name = getattr(type_, '__name__', str(type_))
    return create_model(f'ParsingModel[{type_name}] (for {source})', obj=(type_, ...))


T = TypeVar('T')


def parse_as_type(obj: Any, type_: Type[T]) -> T:
    model_type = _get_parsing_type(type_, source=parse_as_type.__name__)
    return model_type(obj=obj).obj
