"""
Benchmarks for *building* validators and serializers (`SchemaValidator(...)` / `SchemaSerializer(...)`), which is
what dominates class-creation (import) time of applications defining many models.

The schemas mimic what pydantic generates for `BaseModel` subclasses: `model` / `model-fields` nodes with per-field
aliases and metadata, defaults, optionals, containers, literals, unions, nested (already built) models reused as
prebuilt validators, recursive references through definitions, a few validator functions, and a per-model config.
"""

from __future__ import annotations

import gc
from collections.abc import Callable
from typing import Any

import pydantic_core
import pytest
from pydantic_core import SchemaSerializer, SchemaValidator
from pydantic_core import core_schema as cs

_gather = getattr(pydantic_core._pydantic_core, '_gather_schemas_for_cleaning', None)


class _Base:
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'


def _camel(name: str) -> str:
    first, *rest = name.split('_')
    return first + ''.join(part.capitalize() for part in rest)


def _field(schema: cs.CoreSchema, name: str) -> cs.ModelField:
    alias = _camel(name)
    return cs.model_field(schema, validation_alias=alias, serialization_alias=alias, metadata={})


def _optional(schema: cs.CoreSchema) -> cs.CoreSchema:
    return cs.with_default_schema(cs.nullable_schema(schema), default=None)


def _meta_dict() -> cs.CoreSchema:
    return _optional(cs.dict_schema(cs.str_schema(), cs.any_schema()))


def _model(
    name: str,
    fields: dict[str, cs.CoreSchema],
    *,
    ref: bool = True,
    validators: bool = False,
) -> tuple[type, cs.CoreSchema, cs.CoreConfig]:
    cls = type(name, (_Base,), {})
    config = cs.CoreConfig(title=name, validate_by_alias=True, validate_by_name=True)
    model_fields = {field_name: _field(schema, field_name) for field_name, schema in fields.items()}
    schema = cs.model_schema(
        cls,
        cs.model_fields_schema(model_fields, model_name=name, computed_fields=[]),
        custom_init=False,
        root_model=False,
        config=config,
        ref=f'{__name__}.{name}:{id(cls)}' if ref else None,
        metadata={'pydantic_js_functions': [cls.__repr__]},
    )
    if validators:

        def check(value: Any, info: cs.ValidationInfo) -> Any:
            return value

        def before(value: Any) -> Any:
            return value

        schema = cs.with_info_after_validator_function(check, schema, field_name=None)
        schema = cs.no_info_before_validator_function(before, schema)
    return cls, schema, config


def _complete(cls: type, schema: cs.CoreSchema, config: cs.CoreConfig) -> None:
    """What pydantic does once a class is built, so that later references reuse the built objects."""
    cls.__pydantic_validator__ = SchemaValidator(schema, config)
    cls.__pydantic_serializer__ = SchemaSerializer(schema, config)
    cls.__pydantic_complete__ = True


def representative_schemas() -> list[tuple[type, cs.CoreSchema, cs.CoreConfig]]:
    """~40 model schemas of various shapes, in definition order (nested models are complete when referenced)."""
    out: list[tuple[type, cs.CoreSchema, cs.CoreConfig]] = []

    def add(*args: Any, **kwargs: Any) -> cs.CoreSchema:
        cls, schema, config = _model(*args, **kwargs)
        _complete(cls, schema, config)
        out.append((cls, schema, config))
        return schema

    annotations = add(
        'Annotations',
        {
            'audience': _optional(cs.list_schema(cs.literal_schema(['user', 'assistant']))),
            'priority': _optional(cs.float_schema(ge=0, le=1)),
            'last_modified': _optional(cs.str_schema()),
        },
    )
    text = add(
        'TextContent',
        {
            'type': cs.with_default_schema(cs.literal_schema(['text']), default='text'),
            'text': cs.str_schema(),
            'annotations': _optional(annotations),
            'meta': _meta_dict(),
        },
    )
    image = add(
        'ImageContent',
        {
            'type': cs.with_default_schema(cs.literal_schema(['image']), default='image'),
            'data': cs.str_schema(),
            'mime_type': cs.str_schema(),
            'annotations': _optional(annotations),
            'meta': _meta_dict(),
        },
    )
    resource = add(
        'Resource',
        {
            'uri': cs.url_schema(),
            'name': cs.str_schema(),
            'title': _optional(cs.str_schema()),
            'description': _optional(cs.str_schema()),
            'size': _optional(cs.int_schema(ge=0)),
            'tags': cs.with_default_schema(cs.list_schema(cs.str_schema()), default_factory=list),
            'meta': _meta_dict(),
        },
        validators=True,
    )
    content = cs.union_schema(
        [text, image, resource],
    )
    tagged = cs.tagged_union_schema({'text': text, 'image': image}, discriminator='type')
    for i in range(6):
        add(
            f'Params{i}',
            {
                'name': cs.str_schema(min_length=1),
                'arguments': _optional(cs.dict_schema(cs.str_schema(), cs.any_schema())),
                'cursor': _optional(cs.str_schema()),
                'level': cs.literal_schema(['debug', 'info', 'warning', 'error']),
                'flag': cs.with_default_schema(cs.bool_schema(), default=False),
                'count': cs.with_default_schema(cs.int_schema(), default=0),
                'ratio': _optional(cs.float_schema()),
                'meta': _meta_dict(),
            },
        )
    for i in range(6):
        add(
            f'Result{i}',
            {
                'content': cs.list_schema(content),
                'first': _optional(tagged),
                'structured_content': _optional(cs.dict_schema(cs.str_schema(), cs.any_schema())),
                'is_error': cs.with_default_schema(cs.bool_schema(), default=False),
                'result_type': cs.with_default_schema(cs.literal_schema(['complete', 'partial']), default='complete'),
                'meta': _meta_dict(),
            },
        )
    for i in range(6):
        params = out[4 + i][1]
        add(
            f'Request{i}',
            {
                'jsonrpc': cs.literal_schema(['2.0']),
                'id': cs.union_schema([cs.int_schema(), cs.str_schema()]),
                'method': cs.literal_schema([f'things/do{i}']),
                'params': _optional(params),
            },
        )
    # recursive: a tree node referring to itself through a definition
    node_cls, node_schema, node_config = _model(
        'Node',
        {
            'name': cs.str_schema(),
            'children': cs.with_default_schema(
                cs.list_schema(cs.definition_reference_schema('Node')), default_factory=list
            ),
            'parent_name': _optional(cs.str_schema()),
        },
        ref=False,
    )
    node_schema['ref'] = 'Node'
    node_definitions = cs.definitions_schema(cs.definition_reference_schema('Node'), [node_schema])
    _complete(node_cls, node_definitions, node_config)
    out.append((node_cls, node_definitions, node_config))
    for i in range(6):
        add(
            f'Notification{i}',
            {
                'method': cs.literal_schema([f'notifications/n{i}']),
                'node': _optional(cs.definitions_schema(cs.definition_reference_schema('Node'), [node_schema])),
                'data': cs.with_default_schema(cs.any_schema(), default=None),
                'names': _optional(cs.list_schema(cs.str_schema(max_length=100))),
                'mapping': cs.with_default_schema(
                    cs.dict_schema(cs.str_schema(), cs.union_schema([cs.int_schema(), cs.str_schema()])),
                    default_factory=dict,
                ),
            },
            validators=i % 2 == 0,
        )
    big_fields = {}
    for i in range(40):
        kind = i % 8
        if kind == 0:
            big_fields[f'text_field_{i}'] = cs.str_schema()
        elif kind == 1:
            big_fields[f'maybe_number_{i}'] = _optional(cs.int_schema())
        elif kind == 2:
            big_fields[f'flag_value_{i}'] = cs.with_default_schema(cs.bool_schema(), default=True)
        elif kind == 3:
            big_fields[f'items_list_{i}'] = cs.with_default_schema(
                cs.list_schema(cs.str_schema()), default_factory=list
            )
        elif kind == 4:
            big_fields[f'content_{i}'] = _optional(content)
        elif kind == 5:
            big_fields[f'choice_{i}'] = cs.literal_schema(['a', 'b', 'c', 1, 2])
        elif kind == 6:
            big_fields[f'nested_{i}'] = _optional(out[10][1])
        else:
            big_fields[f'meta_{i}'] = _meta_dict()
    add('BigModel', big_fields)
    return out


SCHEMAS = representative_schemas()


def _build_all(constructor: Callable[..., Any]) -> list[Any]:
    """Build each schema as when its class was created: itself incomplete, everything it refers to complete."""
    built = []
    for cls, schema, config in SCHEMAS:
        cls.__pydantic_complete__ = False
        built.append(constructor(schema, config))
        cls.__pydantic_complete__ = True
    return built


def test_build_representative_schemas_work() -> None:
    validators = _build_all(SchemaValidator)
    serializers = _build_all(SchemaSerializer)
    request = validators[16].validate_python(
        {'jsonrpc': '2.0', 'id': 1, 'method': 'things/do0', 'params': {'name': 'x', 'level': 'info'}}
    )
    assert request.params.count == 0
    assert serializers[16].to_python(request, mode='json', by_alias=True)['params']['name'] == 'x'
    node = SCHEMAS[22][0].__pydantic_validator__.validate_python(
        {'name': 'root', 'children': [{'name': 'leaf', 'children': []}]}
    )
    assert node.children[0].parent_name is None
    big = validators[-1].validate_python(
        {_camel(f'text_field_{i}'): 't' for i in range(0, 40, 8)}
        | {_camel(f'choice_{i}'): 'a' for i in range(5, 40, 8)}
    )
    assert serializers[-1].to_python(big)['flag_value_2'] is True


@pytest.mark.benchmark(group='build')
def test_build_model_validators(benchmark: Callable[..., Any]) -> None:
    benchmark(_build_all, SchemaValidator)


@pytest.mark.benchmark(group='build')
def test_build_model_serializers(benchmark: Callable[..., Any]) -> None:
    benchmark(_build_all, SchemaSerializer)


@pytest.mark.benchmark(group='build')
def test_build_model_validators_no_prebuilt(benchmark: Callable[..., Any]) -> None:
    """As during `model_rebuild()`: nested models' validators are built again instead of reused."""

    def build() -> list[Any]:
        return [SchemaValidator(schema, config, _use_prebuilt=False) for _cls, schema, config in SCHEMAS]

    benchmark(build)


@pytest.mark.benchmark(group='build')
def test_build_big_model(benchmark: Callable[..., Any]) -> None:
    cls, schema, config = SCHEMAS[-1]

    def build() -> tuple[Any, Any]:
        return SchemaValidator(schema, config), SchemaSerializer(schema, config)

    cls.__pydantic_complete__ = False
    try:
        benchmark(build)
    finally:
        cls.__pydantic_complete__ = True


@pytest.mark.benchmark(group='build')
def test_build_and_collect(benchmark: Callable[..., Any]) -> None:
    """Building plus what the garbage collector then does with the built objects (a young-generation pass)."""

    def build_and_collect() -> int:
        built = _build_all(SchemaValidator) + _build_all(SchemaSerializer)
        collected = gc.collect(0)
        del built
        return collected

    was_enabled = gc.isenabled()
    gc.disable()
    try:
        benchmark(build_and_collect)
    finally:
        if was_enabled:
            gc.enable()


@pytest.mark.skipif(_gather is None, reason='schema gathering helper not available')
@pytest.mark.benchmark(group='build')
def test_gather_schemas_for_cleaning(benchmark: Callable[..., Any]) -> None:
    node_schema = SCHEMAS[22][1]['definitions'][0]
    definitions = {'Node': node_schema}

    def gather_all() -> None:
        for _cls, schema, _config in SCHEMAS:
            _gather(schema, definitions, frozenset())

    gather_all()
    benchmark(gather_all)
