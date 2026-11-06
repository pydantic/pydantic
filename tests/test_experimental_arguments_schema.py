from typing import Annotated, Any, Generic, Literal, TypeVar

import pytest
from pydantic_core import ArgsKwargs, SchemaValidator
from typing_extensions import TypedDict, Unpack

from pydantic import AliasGenerator, BeforeValidator, Field, PydanticUserError, ValidationError, ValidationInfo
from pydantic.experimental.arguments_schema import generate_arguments_schema


def func(p: bool, *args: str, **kwargs: int) -> None: ...


def skip_first_parameter(index: int, name: str, annotation: Any) -> Literal['skip', None]:
    if index == 0:
        return 'skip'


def test_generate_arguments_v3_schema() -> None:
    arguments_schema = generate_arguments_schema(
        func=func,
        parameters_callback=skip_first_parameter,
    )

    val = SchemaValidator(arguments_schema, config={'coerce_numbers_to_str': True})

    args, kwargs = val.validate_json('{"args": ["arg1", 1], "kwargs": {"extra": 1}}')
    assert args == ('arg1', '1')
    assert kwargs == {'extra': 1}

    args, kwargs = val.validate_python({'args': ['arg1', 1], 'kwargs': {'extra': 1}})
    assert args == ('arg1', '1')
    assert kwargs == {'extra': 1}


def test_generate_arguments_schema() -> None:
    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments',
        parameters_callback=skip_first_parameter,
    )

    val = SchemaValidator(arguments_schema, config={'coerce_numbers_to_str': True})

    args, kwargs = val.validate_python(ArgsKwargs(('arg1', 1), {'extra': 1}))
    assert args == ('arg1', '1')
    assert kwargs == {'extra': 1}


# The following tests should be removed in V3, as `@validate_call` will make use of the
# `'arguments-v3'` schema and as such the `@validate_call` tests will cover these cases
# (most of these tests are actually copied over from there):


def test_arguments_v3() -> None:
    def func(a, /, b: Annotated[int, Field(alias='b_alias')], *args: int, c: int = 6) -> None: ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
    )
    val = SchemaValidator(arguments_schema)
    args, kwargs = val.validate_python({'a': 1, 'b_alias': 2, 'args': [3, 4], 'c': 5})

    assert args == (1, 2, 3, 4)
    assert kwargs == {'c': 5}


def test_arguments_v3_alias_generator() -> None:
    def func(*, a: int) -> None: ...

    arguments_schema = generate_arguments_schema(
        func=func, schema_type='arguments-v3', config={'alias_generator': lambda f: 'b'}
    )
    val = SchemaValidator(arguments_schema)
    _, kwargs = val.validate_python({'b': 1})
    assert kwargs == {'a': 1}

    arguments_schema = generate_arguments_schema(
        func=func, schema_type='arguments-v3', config={'alias_generator': AliasGenerator(alias=lambda f: 'b')}
    )
    val = SchemaValidator(arguments_schema)
    _, kwargs = val.validate_python({'b': 1})
    assert kwargs == {'a': 1}


def test_arguments_v3_kwargs_uniform() -> None:
    def func(**kwargs: int) -> None: ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
    )
    val = SchemaValidator(arguments_schema)
    _, kwargs = val.validate_python({'kwargs': {'extra': 1}})

    assert kwargs == {'extra': 1}


@pytest.mark.parametrize(
    ['input', 'json', 'msg'],
    [
        ([1, 2], False, 'Arguments must be a dictionary'),
        ((1, 2), False, 'Arguments must be a dictionary'),
        (1, False, 'Arguments must be a dictionary'),
        ('[1, 2]', True, 'Arguments must be an object'),
    ],
)
def test_arguments_v3_invalid_type(input: Any, json: bool, msg: str) -> None:
    def func(a: int, b: int) -> None: ...

    arguments_schema = generate_arguments_schema(func=func, schema_type='arguments-v3')
    val = SchemaValidator(arguments_schema)

    with pytest.raises(ValidationError) as exc_info:
        val.validate_json(input) if json else val.validate_python(input)

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'arguments_type', 'loc': (), 'msg': msg, 'input': [1, 2] if json else input},
    ]


class _ExtraOptions(TypedDict, total=False, extra_items=Any):
    m: int


def _keyword_only(*, n: int, **kwargs: Any) -> None: ...


def _positional_or_keyword(n: int, **kwargs: Any) -> None: ...


def _unpacked_typed_dict(*, n: int, **kwargs: Unpack[_ExtraOptions]) -> None: ...


@pytest.mark.parametrize('func', [_keyword_only, _positional_or_keyword, _unpacked_typed_dict])
def test_arguments_v3_var_kwargs_overlapping_parameter(func: Any) -> None:
    arguments_schema = generate_arguments_schema(func=func, schema_type='arguments-v3')
    val = SchemaValidator(arguments_schema)

    with pytest.raises(ValidationError) as exc_info:
        val.validate_python({'n': 1, 'kwargs': {'n': 'not-an-int'}})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'multiple_argument_values',
            'loc': ('kwargs', 'n'),
            'msg': 'Got multiple values for argument',
            'input': 'not-an-int',
        },
    ]


def test_arguments_v3_var_kwargs_positional_only_name() -> None:
    def func(n: int, /, **kwargs: Any) -> None: ...

    arguments_schema = generate_arguments_schema(func=func, schema_type='arguments-v3')
    val = SchemaValidator(arguments_schema)

    # Like in Python, the name of a positional-only parameter can be used in variadic keyword arguments:
    assert val.validate_python({'n': 1, 'kwargs': {'n': 'x'}}) == ((1,), {'n': 'x'})


class _Options(TypedDict):
    b: int


def _var_args(a: int = 1, *args: int) -> None: ...


def _var_kwargs_uniform(a: int = 1, **kwargs: int) -> None: ...


def _var_kwargs_unpacked_typed_dict(a: int = 1, **kwargs: Unpack[_Options]) -> None: ...


@pytest.mark.parametrize(
    ['func', 'input', 'expected'],
    [
        (_var_args, {'args': [2, 3]}, ((1, 2, 3), {})),
        (_var_kwargs_uniform, {'kwargs': {'b': 2}}, ((1,), {'b': 2})),
        (_var_kwargs_unpacked_typed_dict, {'kwargs': {'b': 2}}, ((1,), {'b': 2})),
    ],
)
def test_arguments_v3_variadic_after_default(func: Any, input: Any, expected: Any) -> None:
    arguments_schema = generate_arguments_schema(func=func, schema_type='arguments-v3')
    val = SchemaValidator(arguments_schema)

    assert val.validate_python(input) == expected


@pytest.mark.parametrize(
    ['input', 'expected_field_names'],
    [
        (
            {'a': 1, 'b': 2, 'args': [3], 'c': 4, 'kwargs': {'d': 5}},
            ['a', 'b', 'args', 'c', 'kwargs'],
        ),
        (
            ArgsKwargs((1, 2, 3), {'c': 4, 'd': 5}),
            ['a', 'b', 'c', 'args', 'kwargs'],
        ),
    ],
)
def test_arguments_v3_field_name(input: Any, expected_field_names: list[str]) -> None:
    field_names: list[str | None] = []

    def record_field_name(value: Any, info: ValidationInfo) -> Any:
        field_names.append(info.field_name)
        return value

    RecordedInt = Annotated[int, BeforeValidator(record_field_name)]

    def func(a: RecordedInt, /, b: RecordedInt, *args: RecordedInt, c: RecordedInt, **kwargs: RecordedInt) -> None: ...

    arguments_schema = generate_arguments_schema(func=func, schema_type='arguments-v3')
    SchemaValidator(arguments_schema).validate_python(input)

    assert field_names == expected_field_names


def test_unpacked_typed_dict_kwargs_invalid_type() -> None:
    def func(**kwargs: Unpack[int]): ...

    with pytest.raises(PydanticUserError, check=lambda e: e.code == 'unpack-typed-dict'):
        generate_arguments_schema(
            func=func,
            schema_type='arguments-v3',
        )


def test_unpacked_typed_dict_kwargs_overlaps() -> None:
    class TD(TypedDict, total=False):
        a: int
        b: int
        c: int

    def func(a: int, b: int, **kwargs: Unpack[TD]): ...

    with pytest.raises(
        PydanticUserError,
        check=lambda e: (
            e.code == 'overlapping-unpack-typed-dict'
            and e.message == "Typed dictionary 'TD' overlaps with parameters 'a', 'b'"
        ),
    ):
        generate_arguments_schema(
            func=func,
            schema_type='arguments-v3',
        )

    # Works for a pos-only argument
    def func(a: int, /, **kwargs: Unpack[TD]): ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
    )
    val = SchemaValidator(arguments_schema)
    args, kwargs = val.validate_python({'a': 1, 'kwargs': {'a': 2, 'b': 3, 'c': 4}})

    assert args == (1,)
    assert kwargs == {'a': 2, 'b': 3, 'c': 4}


def test_arguments_v3_kwargs_unpacked_typed_dict() -> None:
    def func(**kwargs: int) -> None: ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
    )
    val = SchemaValidator(arguments_schema)
    _, kwargs = val.validate_python({'kwargs': {'extra': 1}})

    assert kwargs == {'extra': 1}


def test_unpacked_generic_typed_dict_kwargs() -> None:
    T = TypeVar('T')

    class TD(TypedDict, Generic[T]):
        t: T

    def func(**kwargs: Unpack[TD[int]]): ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
    )
    val = SchemaValidator(arguments_schema)

    with pytest.raises(ValidationError):
        val.validate_python({'kwargs': {'t': 'not_an_int'}})


def test_multiple_references() -> None:
    class TD(TypedDict):
        pass

    def func(a: TD, b: TD) -> None: ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
    )
    val = SchemaValidator(arguments_schema)
    args, kwargs = val.validate_python({'a': {}, 'b': {}})
    assert args == ({}, {})
    assert kwargs == {}


def test_populate_by_name() -> None:
    """https://github.com/pydantic/pydantic/issues/13687"""

    def func(a: Annotated[int, Field(alias='b')]) -> None: ...

    arguments_schema = generate_arguments_schema(
        func=func,
        schema_type='arguments-v3',
        config={'populate_by_name': True},
    )
    val = SchemaValidator(arguments_schema)
    args, kwargs = val.validate_python({'a': 1})
    assert args == (1,)
    assert kwargs == {}
