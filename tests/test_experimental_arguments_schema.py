import warnings
from typing import Annotated, Any, Generic, Literal, TypeVar

import pytest
from pydantic_core import ArgsKwargs, SchemaValidator
from typing_extensions import TypedDict, Unpack

from pydantic import AliasGenerator, Field, PydanticExperimentalWarning, PydanticUserError, ValidationError

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
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


def test_unpacked_typed_dict_kwargs_invalid_type() -> None:
    def func(**kwargs: Unpack[int]): ...

    with pytest.raises(PydanticUserError) as exc:
        generate_arguments_schema(
            func=func,
            schema_type='arguments-v3',
        )

    assert exc.value.code == 'unpack-typed-dict'


def test_unpacked_typed_dict_kwargs_overlaps() -> None:
    class TD(TypedDict, total=False):
        a: int
        b: int
        c: int

    def func(a: int, b: int, **kwargs: Unpack[TD]): ...

    with pytest.raises(PydanticUserError) as exc:
        generate_arguments_schema(
            func=func,
            schema_type='arguments-v3',
        )

    assert exc.value.code == 'overlapping-unpack-typed-dict'
    assert exc.value.message == "Typed dictionary 'TD' overlaps with parameters 'a', 'b'"

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
