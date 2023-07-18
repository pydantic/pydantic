import gc
import platform
import weakref

import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema


def test_nullable():
    v = SchemaValidator({'type': 'nullable', 'schema': {'type': 'int'}})
    assert v.validate_python(None) is None
    assert v.validate_python(1) == 1
    assert v.validate_python('123') == 123
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('hello')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'hello',
        }
    ]


def test_union_nullable_bool_int():
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'nullable', 'schema': {'type': 'bool'}},
                {'type': 'nullable', 'schema': {'type': 'int'}},
            ],
        }
    )
    assert v.validate_python(None) is None
    assert v.validate_python(True) is True
    assert v.validate_python(1) == 1


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_leak_nullable():
    def fn():
        def validate(v, info):
            return v

        schema = core_schema.general_plain_validator_function(validate)
        schema = core_schema.nullable_schema(schema)

        # If any of the Rust validators don't implement traversal properly,
        # there will be an undetectable cycle created by this assignment
        # which will keep Defaulted alive
        validate.__pydantic_validator__ = SchemaValidator(schema)

        return validate

    cycle = fn()
    ref = weakref.ref(cycle)
    assert ref() is not None

    del cycle
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    gc.collect()

    assert ref() is None
