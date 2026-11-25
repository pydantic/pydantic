
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
import pydantic
from ._utils import get_args as get_args, is_union as is_union, get_origin as get_origin, is_literal_type as is_literal_type
from pydantic import ConfigDict as ConfigDict

def parse_obj(model: type[_ModelT], value: object) -> _ModelT:
    return model.model_validate(value)

def field_get_default(field: FieldInfo) -> Any:
    value = field.get_default()
    from pydantic_core import PydanticUndefined
    if value == PydanticUndefined:
        return None
    return value

def get_model_config(model: type[pydantic.BaseModel]) -> Any:
    return model.model_config

def get_model_fields(model: type[pydantic.BaseModel]) -> dict[str, FieldInfo]:
    return model.model_fields

class GenericModel(pydantic.BaseModel):
    ...
