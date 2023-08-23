"""
Numerous benchmarks of specific functionality.
"""
import decimal
import json
import platform
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, List
from uuid import UUID

import pytest
from dirty_equals import IsStr

import pydantic_core
from pydantic_core import (
    ArgsKwargs,
    PydanticCustomError,
    PydanticKnownError,
    SchemaValidator,
    ValidationError,
    core_schema,
)
from pydantic_core import ValidationError as CoreValidationError

skip_pypy_deep_stack = pytest.mark.skipif(
    platform.python_implementation() == 'PyPy' and pydantic_core._pydantic_core.build_profile == 'debug',
    reason='PyPy does not have enough stack space for Rust debug builds to recurse very deep',
)

skip_wasm_deep_stack = pytest.mark.skipif(
    sys.platform == 'emscripten', reason='wasm does not have enough stack space to recurse very deep'
)


class TestBenchmarkSimpleModel:
    @pytest.fixture(scope='class')
    def core_validator_fs(self):
        class CoreModel:
            __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        return SchemaValidator(
            {
                'type': 'model',
                'cls': CoreModel,
                'schema': {
                    'type': 'model-fields',
                    'fields': {
                        'name': {'type': 'model-field', 'schema': {'type': 'str'}},
                        'age': {'type': 'model-field', 'schema': {'type': 'int'}},
                        'friends': {'type': 'model-field', 'schema': {'type': 'list', 'items_schema': {'type': 'int'}}},
                        'settings': {
                            'type': 'model-field',
                            'schema': {
                                'type': 'dict',
                                'keys_schema': {'type': 'str'},
                                'values_schema': {'type': 'float'},
                            },
                        },
                    },
                },
            }
        )

    data = {'name': 'John', 'age': 42, 'friends': list(range(200)), 'settings': {f'v_{i}': i / 2.0 for i in range(50)}}

    @pytest.mark.benchmark(group='simple model - python')
    def test_core_python_fs(self, core_validator_fs, benchmark):
        m = core_validator_fs.validate_python(self.data)
        assert m.name == 'John'
        assert m.__dict__.keys() == {'name', 'age', 'friends', 'settings'}
        assert m.__pydantic_fields_set__ == {'name', 'age', 'friends', 'settings'}
        benchmark(core_validator_fs.validate_python, self.data)

    @pytest.mark.benchmark(group='simple model - JSON')
    def test_core_json_fs(self, core_validator_fs, benchmark):
        json_data = json.dumps(self.data)
        benchmark(core_validator_fs.validate_json, json_data)


class TestModelLarge:
    @pytest.fixture(scope='class')
    def core_model_validator(self):
        class CoreModel:
            __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        return SchemaValidator(
            {
                'type': 'model',
                'cls': CoreModel,
                'schema': {
                    'type': 'model-fields',
                    'extra_behavior': 'allow',
                    'fields': {f'field_{i}': {'type': 'model-field', 'schema': {'type': 'int'}} for i in range(100)},
                },
            }
        )

    data = {f'field_{99 - i}': i for i in range(100)}
    data['more'] = 'more data'

    @pytest.mark.benchmark(group='large model - python')
    def test_core_python(self, core_model_validator, benchmark):
        m = core_model_validator.validate_python(self.data)
        assert m.field_0 == 99
        assert m.field_1 == 98
        assert m.field_97 == 2
        assert m.__pydantic_extra__ == {'more': 'more data'}
        benchmark(core_model_validator.validate_python, self.data)

    @pytest.mark.benchmark(group='large model - JSON')
    def test_core_json_fs(self, core_model_validator, benchmark):
        json_data = json.dumps(self.data)
        m = core_model_validator.validate_json(json_data)
        assert m.field_0 == 99
        assert m.field_1 == 98
        assert m.field_97 == 2
        assert m.__pydantic_extra__ == {'more': 'more data'}
        benchmark(core_model_validator.validate_json, json_data)


bool_cases = [True, False, 0, 1, '0', '1', 'true', 'false', 'True', 'False']


@pytest.mark.benchmark(group='bool')
def test_bool_core(benchmark):
    schema_validator = SchemaValidator({'type': 'bool'})

    @benchmark
    def t():
        for case in bool_cases:
            schema_validator.validate_python(case)


small_class_data = {'name': 'John', 'age': 42}


@pytest.mark.benchmark(group='create small model')
def test_small_class_core_dict(benchmark):
    model_schema = {
        'type': 'typed-dict',
        'fields': {
            'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
            'age': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
        },
    }
    dict_schema_validator = SchemaValidator(model_schema)
    benchmark(dict_schema_validator.validate_python, small_class_data)


@pytest.mark.benchmark(group='create small model')
def test_small_class_core_model(benchmark):
    class MyCoreModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        # these are here just as decoration
        name: str
        age: int

    model_schema_validator = SchemaValidator(
        {
            'type': 'model',
            'cls': MyCoreModel,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'name': {'type': 'model-field', 'schema': {'type': 'str'}},
                    'age': {'type': 'model-field', 'schema': {'type': 'int'}},
                },
            },
        }
    )
    benchmark(model_schema_validator.validate_python, small_class_data)


@pytest.mark.benchmark(group='string')
def test_core_string_lax(benchmark):
    validator = SchemaValidator(core_schema.str_schema())
    input_str = 'Hello ' * 20

    assert validator.validate_python(input_str) == input_str

    benchmark(validator.validate_python, input_str)


@pytest.mark.benchmark(group='string')
def test_core_string_lax_wrong(benchmark):
    validator = SchemaValidator(core_schema.str_schema())

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        validator.validate_python(123)

    @benchmark
    def t():
        try:
            validator.validate_python(123)
        except ValidationError:
            pass


@pytest.mark.benchmark(group='string')
def test_core_string_strict(benchmark):
    validator = SchemaValidator(core_schema.str_schema(strict=True))
    input_str = 'Hello ' * 20

    assert validator.validate_python(input_str) == input_str

    benchmark(validator.validate_python, input_str)


@pytest.mark.benchmark(group='string')
def test_core_string_strict_wrong(benchmark):
    validator = SchemaValidator(core_schema.str_schema(strict=True))

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        validator.validate_python(123)

    @benchmark
    def t():
        try:
            validator.validate_python(123)
        except ValidationError:
            pass


@pytest.mark.benchmark(group='string')
def test_core_string_strict_wrong_str_e(benchmark):
    validator = SchemaValidator(core_schema.str_schema(strict=True))

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        validator.validate_python(123)

    @benchmark
    def t():
        try:
            validator.validate_python(123)
        except ValidationError as e:
            str(e)


@pytest.mark.benchmark(group='isinstance-string')
def test_isinstance_string_lax_true(benchmark):
    validator = SchemaValidator(core_schema.str_schema())
    input_str = 'Hello ' * 20

    assert validator.isinstance_python(input_str) is True

    benchmark(validator.isinstance_python, input_str)


@pytest.mark.benchmark(group='isinstance-string')
def test_isinstance_string_lax_false(benchmark):
    validator = SchemaValidator(core_schema.str_schema())

    assert validator.isinstance_python(123) is False

    benchmark(validator.isinstance_python, 123)


@pytest.mark.benchmark(group='isinstance-string')
def test_isinstance_string_strict_true(benchmark):
    validator = SchemaValidator(core_schema.str_schema(strict=True))
    input_str = 'Hello ' * 20

    assert validator.isinstance_python(input_str) is True

    benchmark(validator.isinstance_python, input_str)


@pytest.mark.benchmark(group='isinstance-string')
def test_isinstance_string_strict_false(benchmark):
    validator = SchemaValidator(core_schema.str_schema(strict=True))

    assert validator.isinstance_python(123) is False

    benchmark(validator.isinstance_python, 123)


@pytest.fixture
def definition_model_data():
    data = {'width': -1}

    _data = data
    for i in range(pydantic_core._pydantic_core._recursion_limit - 2):
        _data['branch'] = {'width': i}
        _data = _data['branch']
    return data


@skip_pypy_deep_stack
@skip_wasm_deep_stack
@pytest.mark.benchmark(group='recursive model')
def test_definition_model_core(definition_model_data, benchmark):
    class CoreBranch:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    v = SchemaValidator(
        {
            'ref': 'Branch',
            'type': 'model',
            'cls': CoreBranch,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'width': {'type': 'model-field', 'schema': {'type': 'int'}},
                    'branch': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'schema': {
                                'type': 'nullable',
                                'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                            },
                            'default': None,
                        },
                    },
                },
            },
        }
    )
    benchmark(v.validate_python, definition_model_data)


@pytest.mark.benchmark(group='List[TypedDict]')
def test_list_of_dict_models_core(benchmark):
    v = SchemaValidator(
        {
            'type': 'list',
            'items_schema': {
                'type': 'typed-dict',
                'fields': {'width': {'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
            },
        }
    )

    data = [{'width': i} for i in range(100)]
    benchmark(v.validate_python, data)


list_of_ints_data = ([i for i in range(1000)], [str(i) for i in range(1000)])


@pytest.mark.benchmark(group='List[int]')
def test_list_of_ints_core_py(benchmark):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})

    @benchmark
    def t():
        v.validate_python(list_of_ints_data[0])
        v.validate_python(list_of_ints_data[1])


@pytest.mark.benchmark(group='List[int] JSON')
def test_list_of_ints_core_json(benchmark):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})

    json_data = [json.dumps(d) for d in list_of_ints_data]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


@pytest.mark.benchmark(group='List[Any]')
def test_list_of_any_core_py(benchmark):
    v = SchemaValidator({'type': 'list'})

    @benchmark
    def t():
        v.validate_python(list_of_ints_data[0])
        v.validate_python(list_of_ints_data[1])


set_of_ints_data = ({i for i in range(1000)}, {str(i) for i in range(1000)})
set_of_ints_duplicates = ([i for i in range(100)] * 10, [str(i) for i in range(100)] * 10)


@pytest.mark.benchmark(group='Set[int]')
def test_set_of_ints_core(benchmark):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})

    @benchmark
    def t():
        v.validate_python(set_of_ints_data[0])
        v.validate_python(set_of_ints_data[1])


@pytest.mark.benchmark(group='Set[int]')
def test_set_of_ints_core_duplicates(benchmark):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})

    @benchmark
    def t():
        v.validate_python(set_of_ints_duplicates[0])
        v.validate_python(set_of_ints_duplicates[1])


@pytest.mark.benchmark(group='Set[int]')
def test_set_of_ints_core_length(benchmark):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}, 'max_length': 2000})

    @benchmark
    def t():
        v.validate_python(set_of_ints_data[0])
        v.validate_python(set_of_ints_data[1])


@pytest.mark.benchmark(group='Set[int] JSON')
def test_set_of_ints_core_json(benchmark):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})

    json_data = [json.dumps(list(d)) for d in set_of_ints_data]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


@pytest.mark.benchmark(group='Set[int] JSON')
def test_set_of_ints_core_json_duplicates(benchmark):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})

    json_data = [json.dumps(list(d)) for d in set_of_ints_duplicates]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


frozenset_of_ints = frozenset({i for i in range(1000)})
frozenset_of_ints_duplicates = [i for i in range(100)] * 10


@pytest.mark.benchmark(group='FrozenSet[int]')
def test_frozenset_of_ints_core(benchmark):
    v = SchemaValidator({'type': 'frozenset', 'items_schema': {'type': 'int'}})

    benchmark(v.validate_python, frozenset_of_ints)


@pytest.mark.benchmark(group='FrozenSet[int]')
def test_frozenset_of_ints_duplicates_core(benchmark):
    v = SchemaValidator({'type': 'frozenset', 'items_schema': {'type': 'int'}})

    benchmark(v.validate_python, frozenset_of_ints_duplicates)


dict_of_ints_data = ({str(i): i for i in range(1000)}, {str(i): str(i) for i in range(1000)})


@pytest.mark.benchmark(group='Dict[str, int]')
def test_dict_of_ints_core(benchmark):
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}})

    @benchmark
    def t():
        v.validate_python(dict_of_ints_data[0])
        v.validate_python(dict_of_ints_data[1])


@pytest.mark.benchmark(group='Dict[any, any]')
def test_dict_of_any_core(benchmark):
    v = SchemaValidator({'type': 'dict'})

    @benchmark
    def t():
        v.validate_python(dict_of_ints_data[0])
        v.validate_python(dict_of_ints_data[1])


@pytest.mark.benchmark(group='Dict[str, int] JSON')
def test_dict_of_ints_core_json(benchmark):
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}})

    json_data = [json.dumps(d) for d in dict_of_ints_data]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


many_models_data = [{'age': i} for i in range(1000)]


@pytest.mark.benchmark(group='List[DictSimpleMode]')
def test_many_models_core_dict(benchmark):
    model_schema = {
        'type': 'list',
        'items_schema': {
            'type': 'typed-dict',
            'fields': {'age': {'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
        },
    }
    v = SchemaValidator(model_schema)
    benchmark(v.validate_python, many_models_data)


@pytest.mark.benchmark(group='List[SimpleMode]')
def test_many_models_core_model(benchmark):
    class MyCoreModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    v = SchemaValidator(
        {
            'type': 'list',
            'items_schema': {
                'type': 'model',
                'cls': MyCoreModel,
                'schema': {
                    'type': 'model-fields',
                    'fields': {'age': {'type': 'model-field', 'schema': {'type': 'int'}}},
                },
            },
        }
    )
    benchmark(v.validate_python, many_models_data)


list_of_nullable_data = [None if i % 2 else i for i in range(1000)]


@pytest.mark.benchmark(group='List[Nullable[int]]')
def test_list_of_nullable_core(benchmark):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'nullable', 'schema': {'type': 'int'}}})

    benchmark(v.validate_python, list_of_nullable_data)


some_bytes = b'0' * 1000


@pytest.mark.benchmark(group='bytes')
def test_bytes_core(benchmark):
    v = SchemaValidator({'type': 'bytes'})

    benchmark(v.validate_python, some_bytes)


class TestBenchmarkDateTime:
    @pytest.fixture(scope='class')
    def core_validator(self):
        class CoreModel:
            __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        return SchemaValidator(
            {
                'type': 'model',
                'cls': CoreModel,
                'schema': {
                    'type': 'model-fields',
                    'fields': {'dt': {'type': 'model-field', 'schema': {'type': 'datetime'}}},
                },
            }
        )

    @pytest.fixture(scope='class')
    def datetime_raw(self):
        return datetime.now(timezone.utc) + timedelta(days=1)

    @pytest.fixture(scope='class')
    def datetime_str(self, datetime_raw):
        return str(datetime_raw)

    @pytest.fixture(scope='class')
    def python_data_dict(self, datetime_raw):
        return {'dt': datetime_raw}

    @pytest.fixture(scope='class')
    def json_dict_data(self, datetime_str):
        return json.dumps({'dt': datetime_str})

    @pytest.mark.benchmark(group='datetime model - python')
    def test_core_python(self, core_validator, benchmark, python_data_dict):
        benchmark(core_validator.validate_python, python_data_dict)

    @pytest.mark.benchmark(group='datetime model - JSON')
    def test_model_core_json(self, core_validator, benchmark, json_dict_data):
        benchmark(core_validator.validate_json, json_dict_data)

    @pytest.mark.benchmark(group='datetime datetime')
    def test_core_raw(self, benchmark, datetime_raw):
        v = SchemaValidator({'type': 'datetime'})

        benchmark(v.validate_python, datetime_raw)

    @pytest.mark.benchmark(group='datetime str')
    def test_core_str(self, benchmark, datetime_str):
        v = SchemaValidator({'type': 'datetime'})

        benchmark(v.validate_python, datetime_str)

    @pytest.mark.benchmark(group='datetime future')
    def test_core_future(self, benchmark, datetime_raw):
        v = SchemaValidator({'type': 'datetime', 'gt': datetime.now()})

        benchmark(v.validate_python, datetime_raw)

    @pytest.mark.benchmark(group='datetime future')
    def test_core_future_str(self, benchmark, datetime_str):
        v = SchemaValidator({'type': 'datetime', 'gt': datetime.now()})

        benchmark(v.validate_python, datetime_str)


class TestBenchmarkDateX:
    @pytest.fixture(scope='class')
    def validator(self):
        return SchemaValidator({'type': 'date'})

    @pytest.mark.benchmark(group='date from date')
    def test_date_from_date(self, benchmark, validator):
        benchmark(validator.validate_python, date.today())

    @pytest.mark.benchmark(group='date from str')
    def test_date_from_str(self, benchmark, validator):
        benchmark(validator.validate_python, str(date.today()))

    @pytest.mark.benchmark(group='date from datetime')
    def test_date_from_datetime(self, benchmark, validator):
        benchmark(validator.validate_python, datetime(2000, 1, 1))

    @pytest.mark.benchmark(group='date from datetime str')
    def test_date_from_datetime_str(self, benchmark, validator):
        benchmark(validator.validate_python, str(datetime(2000, 1, 1)))

    @pytest.mark.benchmark(group='date future')
    def test_core_future(self, benchmark):
        v = SchemaValidator({'type': 'date', 'gt': date.today()})

        benchmark(v.validate_python, date(2032, 1, 1))

    @pytest.mark.benchmark(group='date future')
    def test_core_future_str(self, benchmark):
        v = SchemaValidator({'type': 'date', 'gt': date.today()})

        benchmark(v.validate_python, str(date(2032, 1, 1)))


class TestBenchmarkUnion:
    @pytest.mark.benchmark(group='smart-union')
    def test_smart_union_core(self, benchmark):
        v = SchemaValidator({'type': 'union', 'choices': [{'type': 'bool'}, {'type': 'int'}, {'type': 'str'}]})

        benchmark(v.validate_python, 1)

    @pytest.mark.benchmark(group='smart-union-coerce')
    def test_smart_union_coerce_core(self, benchmark):
        v = SchemaValidator({'type': 'union', 'choices': [{'type': 'bool'}, {'type': 'str'}]})

        benchmark(v.validate_python, 1)  # will be True

    @pytest.mark.benchmark(group='strict-union')
    def test_strict_union_core(self, benchmark):
        v = SchemaValidator(
            {'type': 'union', 'strict': True, 'choices': [{'type': 'bool'}, {'type': 'int'}, {'type': 'str'}]}
        )

        benchmark(v.validate_python, 1)

    @pytest.mark.benchmark(group='strict-union-error')
    def test_strict_union_error_core(self, benchmark):
        v = SchemaValidator({'type': 'union', 'strict': True, 'choices': [{'type': 'bool'}, {'type': 'str'}]})

        def validate_with_expected_error():
            try:
                v.validate_python(2)
                assert False
            except CoreValidationError:
                assert True

        benchmark(validate_with_expected_error)


class TestBenchmarkUUID:
    @pytest.fixture(scope='class')
    def core_validator(self):
        class CoreModel:
            __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        return SchemaValidator(
            {
                'type': 'model',
                'cls': CoreModel,
                'schema': {
                    'type': 'model-fields',
                    'fields': {'u': {'type': 'model-field', 'schema': {'type': 'uuid'}}},
                },
            }
        )

    @pytest.fixture(scope='class')
    def validator(self):
        return SchemaValidator({'type': 'uuid'})

    @pytest.fixture(scope='class')
    def pydantic_validator(self):
        def to_UUID(v: Any) -> UUID:
            if isinstance(v, UUID):
                return v
            try:
                if isinstance(v, str):
                    return UUID(v)
                else:
                    try:
                        return UUID(v.decode())
                    except ValueError:
                        # 16 bytes in big-endian order as the bytes argument fail
                        # the above check
                        return UUID(bytes=v)
            except ValueError:
                raise PydanticCustomError(
                    'uuid_parsing', 'Input should be a valid UUID, unable to parse string as an UUID'
                )

        json_schema = core_schema.no_info_after_validator_function(
            to_UUID, core_schema.str_schema(strict=True, strip_whitespace=True)
        )
        schema = core_schema.json_or_python_schema(
            json_schema=json_schema,
            python_schema=core_schema.lax_or_strict_schema(
                lax_schema=core_schema.union_schema([core_schema.is_instance_schema(UUID), json_schema]),
                strict_schema=core_schema.is_instance_schema(UUID),
            ),
            serialization=core_schema.to_string_ser_schema(when_used='json'),
        )

        return SchemaValidator(schema)

    @pytest.mark.benchmark(group='uuid from str')
    def test_uuid_from_string_core(self, benchmark, validator):
        benchmark(validator.validate_python, '12345678-1234-5678-1234-567812345678')

    @pytest.mark.benchmark(group='uuid from str')
    def test_uuid_from_string_pyd(self, benchmark, pydantic_validator):
        benchmark(pydantic_validator.validate_python, '12345678-1234-5678-1234-567812345678')

    @pytest.mark.benchmark(group='uuid from UUID')
    def test_uuid_from_uuid_core(self, benchmark, validator):
        benchmark(validator.validate_python, UUID('12345678-1234-5678-1234-567812345678'))

    @pytest.mark.benchmark(group='uuid from UUID')
    def test_uuid_from_uuid_pyd(self, benchmark, pydantic_validator):
        benchmark(pydantic_validator.validate_python, UUID('12345678-1234-5678-1234-567812345678'))

    @pytest.fixture(scope='class')
    def uuid_raw(self):
        return UUID('12345678-1234-5678-1234-567812345678')

    @pytest.fixture(scope='class')
    def uuid_str(self, uuid_raw):
        return str(uuid_raw)

    @pytest.fixture(scope='class')
    def python_data_dict(self, uuid_raw):
        return {'u': uuid_raw}

    @pytest.fixture(scope='class')
    def json_dict_data(self, uuid_str):
        return json.dumps({'u': uuid_str})

    @pytest.mark.benchmark(group='uuid model - python')
    def test_core_python(self, core_validator, benchmark, python_data_dict):
        benchmark(core_validator.validate_python, python_data_dict)

    @pytest.mark.benchmark(group='uuid model - JSON')
    def test_model_core_json(self, core_validator, benchmark, json_dict_data):
        benchmark(core_validator.validate_json, json_dict_data)

    @pytest.mark.benchmark(group='uuid uuid')
    def test_core_raw(self, benchmark, uuid_raw):
        v = SchemaValidator({'type': 'uuid'})

        benchmark(v.validate_python, uuid_raw)

    @pytest.mark.benchmark(group='uuid str')
    def test_core_str(self, benchmark, uuid_str):
        v = SchemaValidator({'type': 'uuid'})

        benchmark(v.validate_python, uuid_str)


@pytest.mark.benchmark(group='raise-error')
def test_dont_raise_error(benchmark):
    def f(input_value, info):
        return input_value

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'general', 'function': f}})

    @benchmark
    def t():
        v.validate_python(42)


@pytest.mark.benchmark(group='raise-error')
def test_dont_raise_error_no_info(benchmark):
    def f(input_value):
        return input_value

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'no-info', 'function': f}})

    @benchmark
    def t():
        v.validate_python(42)


@pytest.mark.benchmark(group='raise-error')
def test_raise_error_value_error(benchmark):
    def f(input_value, info):
        raise ValueError('this is a custom error')

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'general', 'function': f}})

    @benchmark
    def t():
        try:
            v.validate_python(42)
        except ValidationError:
            pass
        else:
            raise RuntimeError('expected ValidationError')


@pytest.mark.benchmark(group='raise-error')
def test_raise_error_custom(benchmark):
    def f(input_value, info):
        raise PydanticCustomError('my_error', 'this is a custom error {foo}', {'foo': 'FOOBAR'})

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'general', 'function': f}})

    @benchmark
    def t():
        try:
            v.validate_python(42)
        except ValidationError:
            pass
        else:
            raise RuntimeError('expected ValidationError')


@pytest.mark.benchmark(group='tuple')
def test_positional_tuple(benchmark):
    v = SchemaValidator(
        {
            'type': 'tuple-positional',
            'items_schema': [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
        }
    )
    assert v.validate_python((1, 2, 3, '4', 5)) == (1, 2, 3, 4, 5)

    benchmark(v.validate_python, (1, 2, 3, '4', 5))


@pytest.mark.benchmark(group='tuple')
def test_variable_tuple(benchmark):
    v = SchemaValidator({'type': 'tuple-variable', 'items_schema': {'type': 'int'}})
    assert v.validate_python((1, 2, 3, '4', 5)) == (1, 2, 3, 4, 5)

    benchmark(v.validate_python, (1, 2, 3, '4', 5))


@pytest.mark.benchmark(group='tuple-many')
def test_tuple_many_variable(benchmark):
    v = SchemaValidator({'type': 'tuple-variable', 'items_schema': {'type': 'int'}})
    assert v.validate_python(list(range(10))) == tuple(range(10))

    benchmark(v.validate_python, list(range(10)))


@pytest.mark.benchmark(group='tuple-many')
def test_tuple_many_positional(benchmark):
    v = SchemaValidator({'type': 'tuple-positional', 'items_schema': [], 'extras_schema': {'type': 'int'}})
    assert v.validate_python(list(range(10))) == tuple(range(10))

    benchmark(v.validate_python, list(range(10)))


@pytest.mark.benchmark(group='arguments')
def test_arguments(benchmark):
    v = SchemaValidator(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'args1', 'mode': 'positional_only', 'schema': {'type': 'int'}},
                {'name': 'args2', 'mode': 'positional_only', 'schema': {'type': 'str'}},
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'bool'}},
                {'name': 'b', 'mode': 'keyword_only', 'schema': {'type': 'str'}},
                {'name': 'c', 'mode': 'keyword_only', 'schema': {'type': 'int'}},
            ],
        }
    )
    assert v.validate_python(ArgsKwargs((1, 'a', 'true'), {'b': 'bb', 'c': 3})) == ((1, 'a', True), {'b': 'bb', 'c': 3})

    benchmark(v.validate_python, ArgsKwargs((1, 'a', 'true'), {'b': 'bb', 'c': 3}))


@pytest.mark.benchmark(group='defaults')
def test_with_default(benchmark):
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'name': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default': 'John'},
                }
            },
        }
    )
    assert v.validate_python({'name': 'Foo'}) == {'name': 'Foo'}
    assert v.validate_python({}) == {'name': 'John'}

    @benchmark
    def t():
        v.validate_python({'name': 'Foo'})
        v.validate_python({})


@pytest.mark.benchmark(group='chain')
def test_chain_list(benchmark):
    validator = SchemaValidator(
        {
            'type': 'chain',
            'steps': [
                {'type': 'str'},
                {'type': 'function-plain', 'function': {'type': 'general', 'function': lambda v, info: Decimal(v)}},
            ],
        }
    )
    assert validator.validate_python('42.42') == Decimal('42.42')

    benchmark(validator.validate_python, '42.42')


@pytest.mark.benchmark(group='chain')
def test_chain_function(benchmark):
    validator = SchemaValidator(
        {
            'type': 'function-after',
            'schema': {'type': 'str'},
            'function': {'type': 'general', 'function': lambda v, info: Decimal(v)},
        }
    )
    assert validator.validate_python('42.42') == Decimal('42.42')

    benchmark(validator.validate_python, '42.42')


@pytest.mark.benchmark(group='chain-functions')
def test_chain_two_functions(benchmark):
    validator = SchemaValidator(
        {
            'type': 'chain',
            'steps': [
                {'type': 'str'},
                {'type': 'function-plain', 'function': {'type': 'general', 'function': lambda v, info: Decimal(v)}},
                {'type': 'function-plain', 'function': {'type': 'general', 'function': lambda v, info: v * 2}},
            ],
        }
    )
    assert validator.validate_python('42.42') == Decimal('84.84')

    benchmark(validator.validate_python, '42.42')


@pytest.mark.benchmark(group='chain-functions')
def test_chain_nested_functions(benchmark):
    validator = SchemaValidator(
        {
            'type': 'function-after',
            'schema': {
                'type': 'function-after',
                'schema': {'type': 'str'},
                'function': {'type': 'general', 'function': lambda v, info: Decimal(v)},
            },
            'function': {'type': 'general', 'function': lambda v, info: v * 2},
        }
    )
    assert validator.validate_python('42.42') == Decimal('84.84')

    benchmark(validator.validate_python, '42.42')


def validate_yield(iterable, validator):
    for item in iterable:
        yield validator(item)


def generator_gen_python(v, validator, info):
    try:
        iterable = iter(v)
    except TypeError:
        raise PydanticCustomError('iterable_type', 'Input should be a valid iterable')
    return validate_yield(iterable, validator)


@pytest.mark.benchmark(group='generator')
def test_generator_python(benchmark):
    schema = core_schema.general_wrap_validator_function(generator_gen_python, {'type': 'int'})
    v = SchemaValidator(schema)
    input_value = tuple(range(100))

    assert sum(v.validate_python(input_value)) == 4950

    benchmark(v.validate_python, input_value)


def generator_gen_rust(v, *, validator, **_kwargs):
    try:
        generator = iter(v)
    except TypeError:
        raise PydanticCustomError('generator_type', 'Input should be a valid generator')
    return validator.iter(generator)


@pytest.mark.benchmark(group='generator')
def test_generator_rust(benchmark):
    schema = {'type': 'generator', 'items_schema': {'type': 'int'}}
    v = SchemaValidator(schema)
    input_value = tuple(range(100))

    assert sum(v.validate_python(input_value)) == 4950

    benchmark(v.validate_python, input_value)


@pytest.mark.benchmark(group='isinstance-json')
def test_isinstance_json(benchmark):
    validator = SchemaValidator(core_schema.json_or_python_schema(core_schema.str_schema(), core_schema.int_schema()))
    assert validator.validate_json('"foo"') == 'foo'
    with pytest.raises(ValidationError):
        validator.validate_json('123')

    @benchmark
    def t():
        validator.validate_json('"foo"')


@pytest.mark.benchmark(group='error')
def test_int_error(benchmark):
    validator = SchemaValidator(core_schema.int_schema())
    try:
        validator.validate_python('bar')
    except ValidationError as e:
        # insert_assert(e.errors())
        assert e.errors() == [
            {
                'type': 'int_parsing',
                'loc': (),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'bar',
                'url': IsStr(regex=r'https://errors.pydantic.dev/.*?/v/int_parsing'),
            }
        ]
    else:
        raise AssertionError('ValidationError not raised')

    @benchmark
    def t():
        try:
            validator.validate_python('foobar', strict=True)
        except ValidationError as e:
            e.errors()


@pytest.mark.benchmark(group='definition')
def test_definition_in_tree(benchmark):
    validator = SchemaValidator(core_schema.list_schema(core_schema.int_schema()))
    values = [1, 2, 3.0, '4', '5', '6'] * 1000
    benchmark(validator.validate_python, values)


@pytest.mark.benchmark(group='definition')
def test_definition_out_of_tree(benchmark):
    validator = SchemaValidator(
        core_schema.definitions_schema(
            core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
            [core_schema.int_schema(ref='foobar')],
        )
    )
    values = [1, 2, 3.0, '4', '5', '6'] * 1000
    benchmark(validator.validate_python, values)


@pytest.mark.benchmark(group='model_instance')
def test_model_instance(benchmark):
    class MyModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        def __init__(self, **d):
            self.__dict__ = d
            self.__pydantic_extra__ = {}
            self.__pydantic_fields_set__ = set(d)

    validator = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.int_schema()),
                }
            ),
            revalidate_instances='always',
        )
    )
    m1 = MyModel(foo=1, bar='2')
    m2 = validator.validate_python(m1)
    assert m1 is not m2
    assert m2.foo == 1
    assert m2.bar == 2

    benchmark(validator.validate_python, m1)


@pytest.mark.benchmark(group='model_instance')
def test_model_instance_abc(benchmark):
    import abc

    class MyMeta(abc.ABCMeta):
        def __instancecheck__(self, instance) -> bool:
            return hasattr(instance, '__pydantic_validator__') and super().__instancecheck__(instance)

    class BaseModel(metaclass=MyMeta):
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        __pydantic_validator__ = True

        def __init__(self, **d):
            self.__dict__ = d
            self.__pydantic_extra__ = {}
            self.__pydantic_fields_set__ = set(d)

    class MyModel(BaseModel):
        pass

    validator = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.int_schema()),
                }
            ),
            revalidate_instances='always',
        )
    )
    m1 = MyModel(foo=1, bar='2')
    m2 = validator.validate_python(m1)
    assert m1 is not m2
    assert m2.foo == 1
    assert m2.bar == 2

    assert validator.isinstance_python(m1)

    benchmark(validator.validate_python, m1)


class SomeStrEnum(str, Enum):
    foo = 'foo_val'
    bar = 'bar_val'
    baz = 'baz_val'


LARGE_STR_PREFIX = 'a' * 50


@pytest.mark.benchmark(group='validate_literal')
@pytest.mark.parametrize(
    'allowed_values,input,expected_val_res',
    [
        (list(range(5)), 4, 4),
        ([f'abc{i}' for i in range(5)], 'abc4', 'abc4'),
        ([LARGE_STR_PREFIX + f'{i}' for i in range(5)], f'{LARGE_STR_PREFIX}4', f'{LARGE_STR_PREFIX}4'),
        ([SomeStrEnum.foo, SomeStrEnum.bar], SomeStrEnum.bar, SomeStrEnum.bar),
        (list(range(100)), 5, 5),
        ([f'abc{i}' for i in range(100)], 'abc99', 'abc99'),
        ([LARGE_STR_PREFIX + f'{i}' for i in range(100)], f'{LARGE_STR_PREFIX}99', f'{LARGE_STR_PREFIX}99'),
        (['null', None, -1, SomeStrEnum.baz], None, None),
    ],
    ids=[
        'few_ints',
        'few_small_strings',
        'few_large_strings',
        'few_str_enum',
        'many_ints',
        'many_small_strings',
        'many_large_strings',
        'few_mixed',
    ],
)
@pytest.mark.parametrize('py_or_json', ['python', 'json'])
def test_validate_literal(
    benchmark: Any, allowed_values: List[Any], input: Any, expected_val_res: Any, py_or_json: str
) -> None:
    validator = SchemaValidator(core_schema.literal_schema(expected=allowed_values))

    if py_or_json == 'python':
        res = validator.validate_python(input)
        assert res == expected_val_res

        benchmark(validator.validate_python, input)
    else:
        input_json = json.dumps(input)
        res = validator.validate_json(input_json)
        assert res == expected_val_res

        benchmark(validator.validate_json, input_json)


@pytest.mark.benchmark(group='root_model')
def test_core_root_model(benchmark):
    class MyModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: List[int]

    v = SchemaValidator(
        core_schema.model_schema(MyModel, core_schema.list_schema(core_schema.int_schema()), root_model=True)
    )
    assert v.validate_python([1, 2, '3']).root == [1, 2, 3]
    input_data = list(range(100))
    benchmark(v.validate_python, input_data)


@pytest.mark.benchmark(group='strict_int')
def test_strict_int(benchmark):
    v = SchemaValidator(core_schema.int_schema(strict=True))

    benchmark(v.validate_python, 42)


@pytest.mark.benchmark(group='int_range')
def test_int_range(benchmark):
    v = SchemaValidator(core_schema.int_schema(gt=0, lt=100))

    assert v.validate_python(42) == 42
    with pytest.raises(ValidationError, match='Input should be greater than 0'):
        v.validate_python(0)

    benchmark(v.validate_python, 42)


@pytest.mark.benchmark(group='int_range')
def test_int_range_json(benchmark):
    v = SchemaValidator(core_schema.int_schema(gt=0, lt=100))

    assert v.validate_json('42') == 42
    with pytest.raises(ValidationError, match='Input should be greater than 0'):
        v.validate_python('0')

    benchmark(v.validate_json, '42')


@pytest.mark.benchmark(group='tagged_union_ints')
def test_tagged_union_int_keys_python(benchmark):
    inner_schema = core_schema.typed_dict_schema(
        {
            'x': core_schema.typed_dict_field(core_schema.int_schema()),
            'y': core_schema.typed_dict_field(core_schema.int_schema()),
        }
    )
    v = SchemaValidator(core_schema.tagged_union_schema({x: inner_schema for x in range(1000)}, discriminator='x'))

    payload = {'x': 999, 'y': '1'}
    assert v.validate_python(payload) == {'x': 999, 'y': 1}
    with pytest.raises(
        ValidationError, match="Input tag '1001' found using 'x' does not match any of the expected tags"
    ):
        v.validate_python({'x': 1001, 'y': '1'})

    benchmark(v.validate_python, payload)


@pytest.mark.benchmark(group='tagged_union_ints')
def test_tagged_union_int_keys_json(benchmark):
    inner_schema = core_schema.typed_dict_schema(
        {
            'x': core_schema.typed_dict_field(core_schema.int_schema()),
            'y': core_schema.typed_dict_field(core_schema.int_schema()),
        }
    )
    v = SchemaValidator(core_schema.tagged_union_schema({x: inner_schema for x in range(1000)}, discriminator='x'))

    payload = '{"x": 999, "y": "1"}'
    assert v.validate_json(payload) == {'x': 999, 'y': 1}
    with pytest.raises(
        ValidationError, match="Input tag '1001' found using 'x' does not match any of the expected tags"
    ):
        v.validate_json('{"x": 1001, "y": "1"}')

    benchmark(v.validate_json, payload)


@skip_pypy_deep_stack
@skip_wasm_deep_stack
@pytest.mark.benchmark(group='field_function_validator')
def test_field_function_validator(benchmark) -> None:
    def f(v: int, info: core_schema.FieldValidationInfo) -> int:
        assert info.field_name == 'x'
        return v + 1

    schema: core_schema.CoreSchema = core_schema.int_schema()
    limit = pydantic_core._pydantic_core._recursion_limit - 3

    for _ in range(limit):
        schema = core_schema.field_after_validator_function(f, 'x', schema)

    schema = core_schema.typed_dict_schema({'x': core_schema.typed_dict_field(schema)})

    v = SchemaValidator(schema)
    payload = {'x': 0}
    assert v.validate_python(payload) == {'x': limit}

    benchmark(v.validate_python, payload)


class TestBenchmarkDecimal:
    @pytest.fixture(scope='class')
    def validator(self):
        return SchemaValidator({'type': 'decimal'})

    @pytest.fixture(scope='class')
    def pydantic_validator(self):
        Decimal = decimal.Decimal

        def to_decimal(v: str) -> decimal.Decimal:
            try:
                return Decimal(v)
            except decimal.DecimalException as e:
                raise PydanticCustomError('decimal_parsing', 'Input should be a valid decimal') from e

        primitive_schema = core_schema.union_schema(
            [
                # if it's an int keep it like that and pass it straight to Decimal
                # but if it's not make it a string
                # we don't use JSON -> float because parsing to any float will cause
                # loss of precision
                core_schema.int_schema(strict=True),
                core_schema.str_schema(strict=True, strip_whitespace=True),
                core_schema.no_info_plain_validator_function(str),
            ]
        )
        json_schema = core_schema.no_info_after_validator_function(to_decimal, primitive_schema)
        schema = core_schema.json_or_python_schema(
            json_schema=json_schema,
            python_schema=core_schema.lax_or_strict_schema(
                lax_schema=core_schema.union_schema([core_schema.is_instance_schema(decimal.Decimal), json_schema]),
                strict_schema=core_schema.is_instance_schema(decimal.Decimal),
            ),
            serialization=core_schema.to_string_ser_schema(when_used='json'),
        )

        def check_finite(value: decimal.Decimal) -> decimal.Decimal:
            if not value.is_finite():
                raise PydanticKnownError('finite_number')
            return value

        schema = core_schema.no_info_after_validator_function(check_finite, schema)

        return SchemaValidator(schema)

    @pytest.mark.benchmark(group='decimal from str')
    def test_decimal_from_string_core(self, benchmark, validator):
        benchmark(validator.validate_python, '123.456789')

    @pytest.mark.benchmark(group='decimal from str')
    def test_decimal_from_string_pyd(self, benchmark, pydantic_validator):
        benchmark(pydantic_validator.validate_python, '123.456789')

    @pytest.mark.benchmark(group='decimal from str')
    def test_decimal_from_string_limit(self, benchmark):
        benchmark(decimal.Decimal, '123.456789')
