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
