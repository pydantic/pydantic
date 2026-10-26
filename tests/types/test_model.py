import json
from typing import Annotated, Any

import pytest
from dirty_equals import AnyThing

from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SerializationInfo,
    TypeAdapter,
    ValidationError,
    create_model,
    model_serializer,
)


@pytest.mark.parametrize('config', [True, False, None])
@pytest.mark.parametrize('runtime', [True, False, None])
def test_polymorphic_serialization(config: bool | None, runtime: bool | None) -> None:
    class ModelA(BaseModel):
        if config is not None:
            model_config = ConfigDict(polymorphic_serialization=config)

        a: int

    class ModelB(ModelA):
        b: str

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    serializer = TypeAdapter(ModelA).serializer

    assert serializer.to_python(ModelA(a=123), **kwargs) == {'a': 123}
    assert serializer.to_json(ModelA(a=123), **kwargs) == b'{"a":123}'

    polymorphism_enabled = runtime if runtime is not None else config
    if polymorphism_enabled:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == {'a': 123, 'b': 'test'}
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'{"a":123,"b":"test"}'
    else:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == {'a': 123}
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'{"a":123}'


@pytest.mark.parametrize('config', [True, False, None])
@pytest.mark.parametrize('runtime', [True, False, None])
def test_polymorphic_serialization_with_model_serializer(config: bool, runtime: bool) -> None:
    class ModelA(BaseModel):
        if config is not None:
            model_config = ConfigDict(polymorphic_serialization=config)

        a: int

        @model_serializer
        def serialize(self, info: SerializationInfo) -> str:
            assert info.polymorphic_serialization is runtime
            return 'ModelA'

    class ModelB(ModelA):
        b: str

        @model_serializer
        def serialize(self, info: SerializationInfo) -> str:
            assert info.polymorphic_serialization is runtime
            return 'ModelB'

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    serializer = TypeAdapter(ModelA).serializer

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    assert serializer.to_python(ModelA(a=123), **kwargs) == 'ModelA'
    assert serializer.to_json(ModelA(a=123), **kwargs) == b'"ModelA"'

    polymorphism_enabled = runtime if runtime is not None else config
    if polymorphism_enabled:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == 'ModelB'
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'"ModelB"'
    else:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == 'ModelA'
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'"ModelA"'


def test_extra_with_alias(py_and_json) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: Annotated[int, Field(validation_alias=AliasChoices('alias_1', 'alias_2'))]

    adapter = py_and_json(Model)
    m = adapter.validate_test({'a': 123, 'alias_1': 456, 'alias_2': 789})
    # the alias value is preferred over the field by default
    assert m.a == 456
    # the extra value for `a` is still stored in the extra
    assert m.__pydantic_extra__ == {'a': 123, 'alias_2': 789}


def test_extra_key_and_value_both_error(py_and_json) -> None:
    def reject_bad_keys(v: str) -> str:
        if v.startswith('bad_'):
            raise ValueError(f'bad key: {v}')
        return v

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        __pydantic_extra__: dict[Annotated[str, BeforeValidator(reject_bad_keys)], int]

    adapter = py_and_json(Model)
    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_test({'bad_key': 'not_int'})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'value_error',
            'ctx': {'error': AnyThing()},
            'loc': ('bad_key',),
            'msg': 'Value error, bad key: bad_key',
            'input': 'bad_key',
        },
        {
            'type': 'int_parsing',
            'loc': ('bad_key',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_int',
        },
    ]


def test_field_validation_order(py_and_json) -> None:
    order: list[str] = []

    def record_field(name: str):
        def validator(v: Any) -> Any:
            order.append(name)
            return v

        return validator

    def record_extra_key(v: str) -> str:
        order.append(f'extra:{v}')
        return v

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: Annotated[int, BeforeValidator(record_field('a'))]
        b: Annotated[int, BeforeValidator(record_field('b'))]
        c: Annotated[
            int,
            BeforeValidator(record_field('c')),
            Field(validation_alias=AliasChoices('top_c', AliasPath('nested', 'value'))),
        ]

        __pydantic_extra__: dict[Annotated[str, BeforeValidator(record_extra_key)], Any]

    adapter = py_and_json(Model)
    # interleave extras and plain fields
    # 'top_c' is particularly interesting because it should be used as the value for 'c',
    # both 'c' and 'nested' should be recorded as extras
    m = adapter.validate_test({'extra_1': 'x', 'c': 5, 'a': 1, 'nested': {'value': 99}, 'top_c': 3, 'b': 2})
    assert order == ['a', 'b', 'c', 'extra:extra_1', 'extra:c', 'extra:nested']

    assert m.a == 1
    assert m.b == 2
    assert m.c == 3
    assert m.__pydantic_extra__ == {'extra_1': 'x', 'c': 5, 'nested': {'value': 99}}


def test_path_alias_winner_not_in_extras(py_and_json) -> None:
    """When a path-based alias is the best match for a field,
    the matched input key must NOT also appear in the extras."""

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        c: Annotated[
            int,
            Field(validation_alias=AliasChoices('top_c', AliasPath('nested', 'value'))),
        ]

        __pydantic_extra__: dict[str, Any]

    adapter = py_and_json(Model)
    # "best" alias top_c deliberately not included, the path-pased alias should win
    m = adapter.validate_test({'nested': {'value': 99}})

    assert m.c == 99
    assert m.__pydantic_extra__ == {}


def test_duplicate_extra_keys_in_json_later_wins() -> None:
    """When JSON contains duplicate keys for an extra, the later value must win without
    producing spurious validation errors from the earlier (overwritten) value."""

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        __pydantic_extra__: dict[str, int]

    # the earlier value would fail int validation; it must not produce an error because
    # the later occurrence is what should be retained
    json_input = b'{"x": "not_an_int", "x": 42}'
    m = Model.model_validate_json(json_input)
    assert m.__pydantic_extra__ == {'x': 42}


def test_duplicate_nested_alias_keys_in_json_later_wins() -> None:
    calls: list[Any] = []

    def record(value: Any) -> Any:
        calls.append(value)
        return value

    class Model(BaseModel):
        a: Annotated[int, BeforeValidator(record), Field(validation_alias=AliasPath('payload', 'x'))]

    m = Model.model_validate_json('{"payload": {"x": "invalid", "x": 1}}')
    assert m.a == 1
    assert calls == [1]


@pytest.mark.parametrize('keys', [('x', 'y'), ('y', 'x')])
def test_nested_alias_priority_independent_of_input_order(py_and_json, keys) -> None:
    calls: list[Any] = []

    def record(value: Any) -> Any:
        calls.append(value)
        return value

    class Model(BaseModel):
        a: Annotated[
            int,
            BeforeValidator(record),
            Field(validation_alias=AliasChoices(AliasPath('payload', 'x'), AliasPath('payload', 'y'))),
        ]

    values = {'x': 1, 'y': 'invalid'}
    m = py_and_json(Model).validate_test({'payload': {key: values[key] for key in keys}})
    assert m.a == 1
    assert calls == [1]


def test_nested_alias_shared_by_fields(py_and_json) -> None:
    class Model(BaseModel):
        a: int = Field(validation_alias=AliasPath('payload', 'x'))
        b: int = Field(validation_alias=AliasPath('payload', 'x'))

    m = py_and_json(Model).validate_test({'payload': {'x': 1}})
    assert m.a == 1
    assert m.b == 1
    assert m.model_fields_set == {'a', 'b'}


def test_consumed_alias_root_not_in_extras(py_and_json) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: int = Field(validation_alias=AliasPath('payload', 'x'))
        __pydantic_extra__: dict[str, int]

    m = py_and_json(Model).validate_test({'payload': {'x': 1, 'unused': 2}, 'extra': 3})
    assert m.__pydantic_extra__ == {'extra': 3}
    assert m.model_fields_set == {'a', 'extra'}


def test_fields_validate_in_schema_order_before_extra_values(py_and_json) -> None:
    calls: list[tuple[str, Any]] = []

    def record(name: str):
        def validator(value: Any) -> Any:
            calls.append((name, value))
            return value

        return validator

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: Annotated[int, BeforeValidator(record('a'))]
        b: Annotated[int, BeforeValidator(record('b'))]
        __pydantic_extra__: dict[str, Annotated[int, BeforeValidator(record('extra'))]]

    py_and_json(Model).validate_test({'extra': 3, 'b': 2, 'a': 1})
    assert calls == [('a', 1), ('b', 2), ('extra', 3)]


@pytest.mark.parametrize('mode', ['python', 'json'])
@pytest.mark.parametrize(
    'path,json_input',
    [
        (('payload', 'x'), '{"payload": {"x": 1}, "payload": {}}'),
        (('payload', 'x'), '{"payload": {"x": 1}, "payload": null}'),
        (('payload', 'x'), '{"payload": {"x": 1}, "payload": {"y": 2}}'),
        (('payload', 'inner', 'x'), '{"payload": {"inner": {"x": 1}, "inner": {}}}'),
    ],
)
def test_duplicate_parent_replacement_makes_alias_missing(mode, path, json_input) -> None:
    class Model(BaseModel):
        x: int = Field(validation_alias=AliasPath(*path))

    data = json.loads(json_input)
    with pytest.raises(ValidationError) as exc_info:
        if mode == 'json':
            Model.model_validate_json(json_input)
        else:
            Model.model_validate(data)

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': path, 'msg': 'Field required', 'input': data}
    ]


@pytest.mark.parametrize('mode', ['python', 'json'])
def test_duplicate_parent_replacement_uses_default(mode) -> None:
    class Model(BaseModel):
        x: int = Field(default=42, validation_alias=AliasPath('payload', 'x'))

    json_input = '{"payload": {"x": 1}, "payload": {}}'
    m = Model.model_validate_json(json_input) if mode == 'json' else Model.model_validate(json.loads(json_input))
    assert m.x == 42
    assert m.model_fields_set == set()


@pytest.mark.parametrize('mode', ['python', 'json'])
@pytest.mark.parametrize(
    'json_input',
    [
        '{"fallback": 9, "payload": {"x": 1}, "payload": {}}',
        '{"payload": {"x": 1}, "fallback": 9, "payload": {}}',
        '{"payload": {"x": 1}, "payload": {}, "fallback": 9}',
    ],
)
def test_duplicate_parent_replacement_uses_fallback_alias(mode, json_input) -> None:
    class Model(BaseModel):
        x: int = Field(validation_alias=AliasChoices(AliasPath('payload', 'x'), 'fallback'))

    m = Model.model_validate_json(json_input) if mode == 'json' else Model.model_validate(json.loads(json_input))
    assert m.x == 9
    assert m.model_fields_set == {'x'}


@pytest.mark.parametrize('mode', ['python', 'json'])
@pytest.mark.parametrize('extra_behavior', ['allow', 'forbid'])
@pytest.mark.parametrize('consume_parent', [False, True])
def test_duplicate_parent_replacement_extras(mode, extra_behavior, consume_parent) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(extra=extra_behavior)

        x: int = Field(default=42, validation_alias=AliasPath('payload', 'x'))
        if consume_parent:
            payload: dict[str, Any]

    json_input = '{"payload": {"x": 1}, "payload": {}}'
    validate = Model.model_validate_json if mode == 'json' else Model.model_validate
    input_value = json_input if mode == 'json' else json.loads(json_input)
    if extra_behavior == 'forbid' and not consume_parent:
        with pytest.raises(ValidationError) as exc_info:
            validate(input_value)
        assert exc_info.value.errors(include_url=False) == [
            {'type': 'extra_forbidden', 'loc': ('payload',), 'msg': 'Extra inputs are not permitted', 'input': {}}
        ]
    else:
        m = validate(input_value)
        if consume_parent:
            assert m.payload == {}
            assert m.__pydantic_extra__ == ({} if extra_behavior == 'allow' else None)
        else:
            assert m.__pydantic_extra__ == {'payload': {}}


@pytest.mark.parametrize('by_name', [False, True])
@pytest.mark.parametrize(
    'paths,json_input',
    [
        (
            [('preferred', 'x'), ('fallback', 'x')],
            '{"fallback": {"x": 9}, "preferred": {"x": 1}, "preferred": {}}',
        ),
        (
            [('preferred', 'x'), ('fallback', 'x')],
            '{"fallback": {"x": 9}, "preferred": {"x": 1}, "fallback": {}, "preferred": {}}',
        ),
        (
            [('payload', 'x'), ('payload', 'y')],
            '{"payload": {"x": 1}, "payload": {"y": 2}}',
        ),
        (
            [('payload', 'inner', 'x'), ('payload', 'y')],
            '{"payload": {"y": 9, "inner": {"x": 1}, "inner": {"x": 2}, "inner": {}}}',
        ),
        (
            [('payload', 'inner', 'x'), ('payload', 'y')],
            '{"payload": {"y": 9, "inner": {"x": 1}}, "payload": {"inner": {}, "inner": {"x": 2}}}',
        ),
        (
            [('payload', 0, 'x'), ('payload', -1, 'y')],
            '{"payload": [{"x": 1}], "payload": [{"y": 9}]}',
        ),
        (
            [('payload', 0, 'inner', 'x'), ('payload', -1, 'y')],
            '{"payload": [{"y": 9, "inner": {"x": 1}, "inner": {}}]}',
        ),
        (
            [('payload', 0, 'x'), ('payload', -1, 'y')],
            '{"payload": [{"x": 1, "y": 9}], "payload": null}',
        ),
    ],
)
def test_nested_alias_candidates_survive_only_their_own_subtree(by_name, paths, json_input) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        x: int = Field(default=42, validation_alias=AliasChoices(*(AliasPath(*path) for path in paths)))

    json_input = '{"x": 7, ' + json_input[1:]
    expected = Model.model_validate(json.loads(json_input), by_name=by_name)
    actual = Model.model_validate_json(json_input, by_name=by_name)
    assert actual.x == expected.x
    assert actual.model_fields_set == expected.model_fields_set
    assert actual.__pydantic_extra__ == expected.__pydantic_extra__


@pytest.mark.parametrize('replace_root', [False, True])
def test_duplicate_parent_replacement_many_nested_paths(replace_root) -> None:
    Model = create_model(
        'Model',
        **{
            f'f{i}': (int, Field(default=42, validation_alias=AliasPath('payload', f'k{i}', 'value')))
            for i in range(70)
        },
    )
    original = json.dumps({f'k{i}': {'value': i} for i in range(70)})
    replacement = json.dumps({f'k{i}': {'value': i + 100} for i in range(70)})
    if replace_root:
        json_input = (
            '{"payload": '
            + original
            + ', "payload": {}, "payload": '
            + replacement
            + ', "payload": {"k69": {"value": 9}}}'
        )
    else:
        members = ', '.join(f'"k{i}": {{"value": {i}}}, "k{i}": {{}}' for i in range(70))
        json_input = '{"payload": {' + members + '}}'
    actual = Model.model_validate_json(json_input)
    expected = Model.model_validate(json.loads(json_input))
    assert actual == expected
    assert actual.model_fields_set == ({'f69'} if replace_root else set())
