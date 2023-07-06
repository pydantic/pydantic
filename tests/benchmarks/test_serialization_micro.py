import json
from datetime import date, datetime

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema


class TestBenchmarkSimpleModel:
    @pytest.fixture(scope='class')
    def core_schema(self):
        class CoreModel:
            __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        return {
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
                        'schema': {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'float'}},
                    },
                },
            },
        }

    @pytest.fixture(scope='class')
    def core_validator(self, core_schema):
        return SchemaValidator(core_schema)

    @pytest.fixture(scope='class')
    def core_serializer(self, core_schema):
        return SchemaSerializer(core_schema)

    data = {'name': 'John', 'age': 42, 'friends': list(range(200)), 'settings': {f'v_{i}': i / 2.0 for i in range(50)}}

    @pytest.mark.benchmark(group='serialize simple model - python')
    def test_core_dict(self, core_validator: SchemaValidator, core_serializer: SchemaSerializer, benchmark):
        m = core_validator.validate_python(self.data)
        assert core_serializer.to_python(m) == self.data
        benchmark(core_serializer.to_python, m)

    @pytest.mark.benchmark(group='serialize simple model - python filter')
    def test_core_dict_filter(self, core_validator: SchemaValidator, core_serializer: SchemaSerializer, benchmark):
        m = core_validator.validate_python(self.data)
        exclude = {'age': ..., 'fields': {41, 42}}

        @benchmark
        def _():
            core_serializer.to_python(m, exclude=exclude)

    @pytest.mark.benchmark(group='serialize simple model - JSON')
    def test_core_json(self, core_validator: SchemaValidator, core_serializer: SchemaSerializer, benchmark):
        m = core_validator.validate_python(self.data)
        assert json.loads(core_serializer.to_json(m)) == self.data
        benchmark(core_serializer.to_json, m)


@pytest.mark.benchmark(group='list-of-str')
def test_json_direct_list_str(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'str'}})
    assert serializer.to_json(list(map(str, range(5)))) == b'["0","1","2","3","4"]'

    items = list(map(str, range(1000)))
    benchmark(serializer.to_json, items)


@pytest.mark.benchmark(group='list-of-str')
def test_python_json_list_str(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'str'}})
    assert serializer.to_python(list(map(str, range(5))), mode='json') == ['0', '1', '2', '3', '4']

    items = list(map(str, range(1000)))

    @benchmark
    def t():
        serializer.to_python(items, mode='json')


@pytest.mark.benchmark(group='list-of-str')
def test_json_any_list_str(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'any'}})
    assert serializer.to_json(list(map(str, range(5)))) == b'["0","1","2","3","4"]'

    items = list(map(str, range(1000)))
    benchmark(serializer.to_json, items)


@pytest.mark.benchmark(group='list-of-int')
def test_json_direct_list_int(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'int'}})
    assert serializer.to_json(list(range(5))) == b'[0,1,2,3,4]'

    items = list(range(1000))
    benchmark(serializer.to_json, items)


@pytest.mark.benchmark(group='list-of-int')
def test_json_any_list_int(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'any'}})
    assert serializer.to_json(list(range(5))) == b'[0,1,2,3,4]'

    items = list(range(1000))
    benchmark(serializer.to_json, items)


@pytest.mark.benchmark(group='list-of-int')
def test_python_json_list_int(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'int'}})
    assert serializer.to_python(list(range(5)), mode='json') == [0, 1, 2, 3, 4]

    items = list(range(1000))

    @benchmark
    def t():
        serializer.to_python(items, mode='json')


@pytest.mark.benchmark(group='list-of-bool')
def test_python_json_list_none(benchmark):
    serializer = SchemaSerializer({'type': 'list', 'items_schema': {'type': 'none'}})
    assert serializer.to_python([None, None, None], mode='json') == [None, None, None]

    items = [None for v in range(1000)]

    @benchmark
    def t():
        serializer.to_python(items, mode='json')


@pytest.mark.benchmark(group='date-format')
def test_date_format(benchmark):
    serializer = SchemaSerializer(
        {'type': 'any', 'serialization': {'type': 'format', 'formatting_string': '%Y-%m-%d', 'when_used': 'always'}}
    )
    d = date(2022, 11, 20)
    assert serializer.to_python(d) == '2022-11-20'

    benchmark(serializer.to_python, d)


@pytest.mark.benchmark(group='date-format')
def test_date_format_function(benchmark):
    def fmt(value, info):
        return value.strftime('%Y-%m-%d')

    serializer = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                fmt, info_arg=True, return_schema=core_schema.str_schema()
            )
        )
    )
    d = date(2022, 11, 20)
    assert serializer.to_python(d) == '2022-11-20'

    benchmark(serializer.to_python, d)


@pytest.mark.benchmark(group='date-format')
def test_date_format_function_no_info(benchmark):
    def fmt(value):
        return value.strftime('%Y-%m-%d')

    serializer = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(fmt, return_schema=core_schema.str_schema())
        )
    )
    d = date(2022, 11, 20)
    assert serializer.to_python(d) == '2022-11-20'

    benchmark(serializer.to_python, d)


class BasicModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture(scope='module', name='basic_model_serializer')
def basic_model_serializer_fixture():
    return SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.int_schema()),
                    'b': core_schema.model_field(core_schema.int_schema()),
                    'c': core_schema.model_field(core_schema.int_schema()),
                    'd': core_schema.model_field(core_schema.int_schema()),
                    'e': core_schema.model_field(core_schema.int_schema()),
                    'f': core_schema.model_field(core_schema.int_schema()),
                    'g': core_schema.model_field(core_schema.int_schema()),
                    'h': core_schema.model_field(core_schema.int_schema()),
                }
            ),
        )
    )


@pytest.mark.benchmark(group='model-python')
def test_core_model_py(benchmark, basic_model_serializer):
    m = BasicModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8)
    assert basic_model_serializer.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    benchmark(basic_model_serializer.to_python, m)


@pytest.fixture(scope='module', name='basic_model_serializer_extra')
def basic_model_serializer_extra_fixture():
    return SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.int_schema()),
                    'b': core_schema.model_field(core_schema.int_schema()),
                    'c': core_schema.model_field(core_schema.int_schema()),
                    'd': core_schema.model_field(core_schema.int_schema()),
                    'e': core_schema.model_field(core_schema.int_schema()),
                    'f': core_schema.model_field(core_schema.int_schema()),
                    'g': core_schema.model_field(core_schema.int_schema()),
                    'h': core_schema.model_field(core_schema.int_schema()),
                },
                extra_behavior='allow',
            ),
            extra_behavior='allow',
        )
    )


@pytest.mark.benchmark(group='model-python')
def test_core_model_py_extra(benchmark, basic_model_serializer_extra):
    m = BasicModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, __pydantic_extra__={'i': 9})
    assert basic_model_serializer_extra.to_python(m) == {
        'a': 1,
        'b': 2,
        'c': 3,
        'd': 4,
        'e': 5,
        'f': 6,
        'g': 7,
        'h': 8,
        'i': 9,
    }
    benchmark(basic_model_serializer_extra.to_python, m)


@pytest.mark.benchmark(group='model-json')
def test_core_model_json(benchmark, basic_model_serializer):
    m = BasicModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8)
    assert basic_model_serializer.to_json(m) == b'{"a":1,"b":2,"c":3,"d":4,"e":5,"f":6,"g":7,"h":8}'
    benchmark(basic_model_serializer.to_json, m)


@pytest.mark.benchmark(group='model-json')
def test_core_model_json_extra(benchmark, basic_model_serializer_extra):
    m = BasicModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, __pydantic_extra__={'i': 9})
    assert basic_model_serializer_extra.to_json(m) == b'{"a":1,"b":2,"c":3,"d":4,"e":5,"f":6,"g":7,"h":8,"i":9}'
    benchmark(basic_model_serializer_extra.to_json, m)


class FieldsSetModel:
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture(scope='module', name='fs_model_serializer')
def fs_model_serializer_fixture():
    return SchemaSerializer(
        core_schema.model_schema(
            FieldsSetModel,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.int_schema()),
                    'b': core_schema.model_field(core_schema.int_schema()),
                    'c': core_schema.model_field(core_schema.int_schema()),
                    'd': core_schema.model_field(core_schema.int_schema()),
                    'e': core_schema.model_field(core_schema.int_schema()),
                    'f': core_schema.model_field(core_schema.int_schema()),
                    'g': core_schema.model_field(core_schema.int_schema()),
                    'h': core_schema.model_field(core_schema.int_schema()),
                }
            ),
        )
    )


@pytest.mark.benchmark(group='model-exclude-unset')
def test_model_exclude_unset_false(benchmark, fs_model_serializer):
    m = FieldsSetModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, __pydantic_fields_set__={'a', 'b', 'c', 'd', 'e', 'f'})
    assert fs_model_serializer.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    assert fs_model_serializer.to_python(m, exclude_unset=True) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

    @benchmark
    def r():
        fs_model_serializer.to_python(m)


@pytest.mark.benchmark(group='model-exclude-unset')
def test_model_exclude_unset_true(benchmark, fs_model_serializer):
    m = FieldsSetModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, __pydantic_fields_set__={'a', 'b', 'c', 'd', 'e', 'f'})
    assert fs_model_serializer.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    assert fs_model_serializer.to_python(m, exclude_unset=True) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

    @benchmark
    def r():
        fs_model_serializer.to_python(m, exclude_unset=True)


@pytest.mark.benchmark(group='model-list-json')
def test_model_list_core_json(benchmark):
    s = SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(
                        core_schema.list_schema(
                            core_schema.int_schema(), serialization=core_schema.filter_seq_schema(exclude={1, 2})
                        )
                    )
                }
            ),
        )
    )

    m = BasicModel(a=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert s.to_json(m) == b'{"a":[0,3,4,5,6,7,8,9]}'

    m_big = BasicModel(a=list(range(1000)))
    j = s.to_json(m_big)
    assert j.startswith(b'{"a":[0,3,4')
    assert j.endswith(b'998,999]}')

    @benchmark
    def r():
        s.to_json(m_big)


@pytest.mark.benchmark(group='model-list-json')
def test_datetime(benchmark):
    v = SchemaSerializer(core_schema.datetime_schema())
    d = datetime(2022, 12, 2, 12, 13, 14)
    assert v.to_python(d, mode='json') == '2022-12-02T12:13:14'

    @benchmark
    def r():
        v.to_python(d, mode='json')


@pytest.mark.benchmark(group='to-string')
def test_to_string_format(benchmark):
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.format_ser_schema('d')))
    assert s.to_json(123) == b'"123"'

    benchmark(s.to_json, 123)


@pytest.mark.benchmark(group='to-string')
def test_to_string_direct(benchmark):
    s = SchemaSerializer(core_schema.any_schema(serialization={'type': 'to-string'}))
    assert s.to_json(123) == b'"123"'

    benchmark(s.to_json, 123)


def test_filter(benchmark):
    v = SchemaSerializer(core_schema.list_schema(core_schema.any_schema()))
    assert v.to_python(['a', 'b', 'c', 'd', 'e'], include={-1, -2}) == ['d', 'e']

    @benchmark
    def t():
        v.to_python(['a', 'b', 'c', 'd', 'e'], include={-1, -2})
