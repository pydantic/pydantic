from functools import lru_cache
from typing import Any, Type, TypeVar

from pydantic.utils import lenient_issubclass

from .fields import Field

__all__ = ('parse_as_type', 'dump_as_type')


@lru_cache(maxsize=None)
def _get_parsing_type(type_: Any, source: str) -> Any:
    from pydantic.main import create_model

    type_name = getattr(type_, '__name__', str(type_))
    return create_model(f'ParsingModel[{type_name}] (for {source})', obj=(type_, ...))


T = TypeVar('T')


def parse_as_type(obj: Any, type_: Type[T]) -> T:
    model_type = _get_parsing_type(type_, source=parse_as_type.__name__)
    return model_type(obj=obj).obj


def dump_as_type(obj: T, type_: Type[T]) -> Any:
    model_type = _get_parsing_type(type_, source=dump_as_type.__name__)
    model = model_type(obj=obj)
    model_dict = model.dict(as_type=model_type)
    return model_dict['obj']


def requires_casting(obj: Any, old_field: Field, new_field: Field) -> bool:
    from pydantic.main import BaseModel

    if old_field.type_ != new_field.type_:
        return True
    if lenient_issubclass(old_field.type_, BaseModel):
        return type(obj) != old_field.type_
    return False
