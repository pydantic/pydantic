# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
import sys
from collections.abc import Callable
from typing import Annotated, Any, cast
from pydantic import BaseModel, ConfigDict, PrivateAttr, TypeAdapter, WithJsonSchema
from pydantic.json_schema import GenerateJsonSchema
from typing_extensions import NotRequired, ReadOnly, TypedDict, get_type_hints, is_typeddict
from typing_inspection.introspection import AnnotationSource, inspect_annotation

class StrictJsonSchema(GenerateJsonSchema):
    pass
_LOCAL_DEFS_PREFIX = '#/$defs/'

def _inline_root_ref(schema: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get('$ref')
    if not isinstance(ref, str) or not ref.startswith(_LOCAL_DEFS_PREFIX):
        return schema
    definition = cast(dict[str, Any], schema['$defs'][ref.removeprefix(_LOCAL_DEFS_PREFIX)])
    siblings = {key: value for key, value in schema.items() if key != '$ref'}
    return {**definition, **siblings}

class ArgModelBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

class FuncMetadata(BaseModel):
    arg_model: Annotated[type[ArgModelBase], WithJsonSchema(None)]
    output_schema: dict[str, Any] | None = None
    output_model: Annotated[Any, WithJsonSchema(None)] = None
    wrap_output: bool = False
    _adapter: tuple[Any, TypeAdapter[Any]] | None = PrivateAttr(default=None)

    def model_post_init(self, context: Any, /) -> None:
        if self.output_model is not None and self.output_schema is None:
            schema = self._output_adapter(self.output_model).json_schema(schema_generator=StrictJsonSchema)
            self.output_schema = _inline_root_ref(schema)

    def _output_adapter(self, output_model: Any) -> TypeAdapter[Any]:
        if self._adapter is None or self._adapter[0] is not output_model:
            self._adapter = (output_model, TypeAdapter(_pydantic_readable_typeddict(output_model)))
        return self._adapter[1]
    model_config = ConfigDict(arbitrary_types_allowed=True)

def _pydantic_readable_typeddict(output_model: type[Any]) -> type[Any]:
    if sys.version_info >= (3, 12) or not is_typeddict(output_model) or type(output_model).__module__ != 'typing':
        return output_model
    return _as_typing_extensions_typeddict(output_model)

def _as_typing_extensions_typeddict(td_type: type[Any]) -> type[Any]:
    items: dict[str, Any] = {}
    for name, hint in get_type_hints(td_type, include_extras=True).items():
        key = inspect_annotation(hint, annotation_source=AnnotationSource.TYPED_DICT)
        item: Any = Annotated[(key.type, *key.metadata)] if key.metadata else key.type
        if 'read_only' in key.qualifiers:
            item = ReadOnly[item]
        required = (name in td_type.__required_keys__ or 'required' in key.qualifiers) and 'not_required' not in key.qualifiers
        items[name] = item if required else NotRequired[item]
    rebuilt = cast('Callable[[str, dict[str, Any]], type[Any]]', TypedDict)(td_type.__name__, items)
    for attr in ('__doc__', '__module__', '__qualname__', '__pydantic_config__'):
        if hasattr(td_type, attr):
            setattr(rebuilt, attr, getattr(td_type, attr))
    return rebuilt
