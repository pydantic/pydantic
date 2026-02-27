import pytest

from pydantic_core import SchemaError, SchemaValidator
from pydantic_core import core_schema as cs


def test_build_non_default_follows_default() -> None:
    with pytest.raises(SchemaError, match="Required parameter 'b' follows parameter with default"):
        SchemaValidator(
            schema=cs.arguments_v3_schema(
                [
                    cs.arguments_v3_parameter(
                        name='a',
                        schema=cs.with_default_schema(schema=cs.int_schema(), default_factory=lambda: 42),
                        mode='positional_or_keyword',
                    ),
                    cs.arguments_v3_parameter(name='b', schema=cs.int_schema(), mode='positional_or_keyword'),
                ]
            )
        )


def test_duplicate_parameter_name() -> None:
    with pytest.raises(SchemaError, match="Duplicate parameter 'test'"):
        SchemaValidator(
            schema=cs.arguments_v3_schema(
                [
                    cs.arguments_v3_parameter(name='test', schema=cs.int_schema()),
                    cs.arguments_v3_parameter(name='a', schema=cs.int_schema()),
                    cs.arguments_v3_parameter(name='test', schema=cs.int_schema()),
                ]
            )
        )


def test_invalid_positional_only_parameter_position() -> None:
    with pytest.raises(SchemaError, match="Positional only parameter 'test' cannot follow other parameter kinds"):
        SchemaValidator(
            schema=cs.arguments_v3_schema(
                [
                    cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='var_args'),
                    cs.arguments_v3_parameter(name='test', schema=cs.int_schema(), mode='positional_only'),
                ]
            )
        )


def test_invalid_positional_or_keyword_parameter_position() -> None:
    with pytest.raises(
        SchemaError, match="Positional or keyword parameter 'test' cannot follow variadic or keyword only parameters"
    ):
        SchemaValidator(
            schema=cs.arguments_v3_schema(
                [
                    cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='var_args'),
                    cs.arguments_v3_parameter(name='test', schema=cs.int_schema(), mode='positional_or_keyword'),
                ]
            )
        )


def test_invalid_var_args_parameter_position() -> None:
    with pytest.raises(
        SchemaError, match="Variadic positional parameter 'test' cannot follow variadic or keyword only parameters"
    ):
        SchemaValidator(
            schema=cs.arguments_v3_schema(
                [
                    cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='keyword_only'),
                    cs.arguments_v3_parameter(name='test', schema=cs.int_schema(), mode='var_args'),
                ]
            )
        )


def test_invalid_keyword_only_parameter_position() -> None:
    with pytest.raises(
        SchemaError, match="Keyword only parameter 'test' cannot follow variadic keyword only parameter"
    ):
        SchemaValidator(
            schema=cs.arguments_v3_schema(
                [
                    cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='var_kwargs_uniform'),
                    cs.arguments_v3_parameter(name='test', schema=cs.int_schema(), mode='keyword_only'),
                ]
            )
        )
