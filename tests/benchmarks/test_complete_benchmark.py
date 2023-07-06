"""
General benchmarks that attempt to cover all field types, through by no means all uses of all field types.
"""
import json
from datetime import date, datetime, time

import pytest

from pydantic_core import SchemaValidator, ValidationError

from .complete_schema import input_data_lax, input_data_strict, input_data_wrong, schema


def test_complete_valid():
    lax_schema = schema()
    cls = lax_schema['cls']
    lax_validator = SchemaValidator(lax_schema)
    output = lax_validator.validate_python(input_data_lax())
    assert isinstance(output, cls)
    assert len(output.__pydantic_fields_set__) == 39
    output_dict = output.__dict__
    assert output_dict == {
        'field_str': 'fo',
        'field_str_con': 'fooba',
        'field_int': 1,
        'field_int_con': 8,
        'field_float': 1.0,
        'field_float_con': 10.0,
        'field_bool': True,
        'field_bytes': b'foobar',
        'field_bytes_con': b'foobar',
        'field_date': date(2010, 2, 3),
        'field_date_con': date(2020, 1, 1),
        'field_time': time(12, 0),
        'field_time_con': time(12, 0),
        'field_datetime': datetime(2020, 1, 1, 12, 13, 14),
        'field_datetime_con': datetime(2020, 1, 1),
        'field_list_any': ['a', b'b', True, 1.0, None] * 10,
        'field_list_str': ['a', 'b', 'c'] * 10,
        'field_list_str_con': ['a', 'b', 'c'] * 10,
        'field_set_any': {'a', b'b', True, 1.0, None},
        'field_set_int': set(range(100)),
        'field_set_int_con': set(range(42)),
        'field_frozenset_any': frozenset({'a', b'b', True, 1.0, None}),
        'field_frozenset_bytes': frozenset([f'{i}'.encode() for i in range(100)]),
        'field_frozenset_bytes_con': frozenset([f'{i}'.encode() for i in range(42)]),
        'field_tuple_var_len_any': ('a', b'b', True, 1.0, None),
        'field_tuple_var_len_float': tuple((i + 0.5 for i in range(100))),
        'field_tuple_var_len_float_con': tuple((i + 0.5 for i in range(42))),
        'field_tuple_fix_len': ('a', 1, 1.0, True),
        'field_dict_any': {'a': 'b', 1: True, 1.0: 1.0},
        'field_dict_str_float': {f'{i}': i + 0.5 for i in range(100)},
        'field_literal_1_int': 1,
        'field_literal_1_str': 'foobar',
        'field_literal_mult_int': 3,
        'field_literal_mult_str': 'foo',
        'field_literal_assorted': 'foo',
        'field_list_nullable_int': [1, None, 2, None, 3, None, 4, None],
        'field_union': {'field_str': 'foo', 'field_int': 1, 'field_float': 1.0},
        'field_functions_model': {
            'field_before': 'foo Changed',
            'field_after': 'foo Changed',
            'field_wrap': 'Input foo Changed',
            'field_plain': 'foo Changed',
        },
        'field_recursive': {
            'name': 'foo',
            'sub_branch': {'name': 'bar', 'sub_branch': {'name': 'baz', 'sub_branch': None}},
        },
    }

    strict_validator = SchemaValidator(schema(strict=True))
    output2 = strict_validator.validate_python(input_data_strict())
    assert output_dict == output2.__dict__


def test_complete_invalid():
    lax_schema = schema()
    lax_validator = SchemaValidator(lax_schema)
    with pytest.raises(ValidationError) as exc_info:
        lax_validator.validate_python(input_data_wrong())
    assert len(exc_info.value.errors(include_url=False)) == 738


@pytest.mark.benchmark(group='complete')
def test_complete_core_lax(benchmark):
    v = SchemaValidator(schema())
    benchmark(v.validate_python, input_data_lax())


@pytest.mark.benchmark(group='complete')
def test_complete_core_strict(benchmark):
    v = SchemaValidator(schema(strict=True))
    benchmark(v.validate_python, input_data_strict())


@pytest.mark.benchmark(group='complete-wrong')
def test_complete_core_error(benchmark):
    v = SchemaValidator(schema())
    data = input_data_wrong()

    @benchmark
    def f():
        try:
            v.validate_python(data)
        except ValueError:
            pass
        else:
            raise RuntimeError('expected ValueError')


@pytest.mark.benchmark(group='complete-wrong')
def test_complete_core_isinstance(benchmark):
    v = SchemaValidator(schema())
    data = input_data_wrong()
    assert v.isinstance_python(data) is False

    @benchmark
    def f():
        v.isinstance_python(data)


def default_json_encoder(obj):
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    else:
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')


@pytest.mark.benchmark(group='complete-json')
def test_complete_core_json(benchmark):
    v = SchemaValidator(schema())
    json_data = json.dumps(input_data_lax(), default=default_json_encoder)
    benchmark(v.validate_json, json_data)


@pytest.mark.benchmark(group='build')
def test_build_schema(benchmark):
    lax_schema = schema()
    benchmark(SchemaValidator, lax_schema)
