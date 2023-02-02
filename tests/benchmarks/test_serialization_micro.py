import json
from datetime import date, datetime
from typing import Dict, List

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

from .test_micro_benchmarks import BaseModel, skip_pydantic


class TestBenchmarkSimpleModel:
    @pytest.fixture(scope='class')
    def pydantic_model(self):
        class PydanticModel(BaseModel):
            name: str
            age: int
            friends: List[int]
            settings: Dict[str, float]

        return PydanticModel

    @pytest.fixture(scope='class')
    def core_schema(self):
        class CoreModel:
            __slots__ = '__dict__', '__fields_set__'

        return {
            'type': 'model',
            'cls': CoreModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {
                    'name': {'schema': {'type': 'str'}},
                    'age': {'schema': {'type': 'int'}},
                    'friends': {'schema': {'type': 'list', 'items_schema': {'type': 'int'}}},
                    'settings': {
                        'schema': {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'float'}}
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

    @skip_pydantic
    @pytest.mark.benchmark(group='serialize simple model - python')
    def test_v1_dict(self, pydantic_model, benchmark):
        m = pydantic_model(**self.data)
        assert m.dict() == self.data
        benchmark(m.dict)

    @pytest.mark.benchmark(group='serialize simple model - python')
    def test_core_dict(self, core_validator: SchemaValidator, core_serializer: SchemaSerializer, benchmark):
        m = core_validator.validate_python(self.data)
        assert core_serializer.to_python(m) == self.data
        benchmark(core_serializer.to_python, m)

    @skip_pydantic
    @pytest.mark.benchmark(group='serialize simple model - python filter')
    def test_v1_dict_filter(self, pydantic_model, benchmark):
        m = pydantic_model(**self.data)
        assert m.dict() == self.data
        exclude = {'age': ..., 'fields': {41, 42}}

        @benchmark
        def _():
            m.dict(exclude=exclude)

    @pytest.mark.benchmark(group='serialize simple model - python filter')
    def test_core_dict_filter(self, core_validator: SchemaValidator, core_serializer: SchemaSerializer, benchmark):
        m = core_validator.validate_python(self.data)
        exclude = {'age': ..., 'fields': {41, 42}}
        # assert core_serializer.to_python(m, exclude=exclude) == pydantic_model(**self.data).dict(exclude=exclude)

        @benchmark
        def _():
            core_serializer.to_python(m, exclude=exclude)

    @skip_pydantic
    @pytest.mark.benchmark(group='serialize simple model - JSON')
    def test_v1_json(self, pydantic_model, benchmark):
        m = pydantic_model(**self.data)
        assert json.loads(m.json()) == self.data
        benchmark(m.json)

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
        core_schema.any_schema(serialization=core_schema.function_plain_ser_schema(fmt, json_return_type='str'))
    )
    d = date(2022, 11, 20)
    assert serializer.to_python(d) == '2022-11-20'

    benchmark(serializer.to_python, d)


@pytest.fixture(scope='module', name='v1_model')
def v1_model_fixture():
    class PydanticModel(BaseModel):
        a: int
        b: int
        c: int
        d: int
        e: int
        f: int
        g: int
        h: int

    return PydanticModel


@skip_pydantic
@pytest.mark.benchmark(group='model-python')
def test_model_v1_py(benchmark, v1_model):
    m = v1_model(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8)
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    benchmark(m.dict)


@skip_pydantic
@pytest.mark.benchmark(group='model-json')
def test_model_v1_json(benchmark, v1_model):
    m = v1_model(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8)
    assert m.json() == '{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8}'
    benchmark(m.json)


class BasicModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture(scope='module', name='basic_model_serializer')
def basic_model_serializer_fixture():
    return SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(core_schema.int_schema()),
                    'b': core_schema.typed_dict_field(core_schema.int_schema()),
                    'c': core_schema.typed_dict_field(core_schema.int_schema()),
                    'd': core_schema.typed_dict_field(core_schema.int_schema()),
                    'e': core_schema.typed_dict_field(core_schema.int_schema()),
                    'f': core_schema.typed_dict_field(core_schema.int_schema()),
                    'g': core_schema.typed_dict_field(core_schema.int_schema()),
                    'h': core_schema.typed_dict_field(core_schema.int_schema()),
                }
            ),
        )
    )


@pytest.mark.benchmark(group='model-python')
def test_core_model_py(benchmark, basic_model_serializer):
    m = BasicModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8)
    assert basic_model_serializer.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    benchmark(basic_model_serializer.to_python, m)


@pytest.mark.benchmark(group='model-json')
def test_core_model_json(benchmark, basic_model_serializer):
    m = BasicModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8)
    assert basic_model_serializer.to_json(m) == b'{"a":1,"b":2,"c":3,"d":4,"e":5,"f":6,"g":7,"h":8}'
    benchmark(basic_model_serializer.to_json, m)


class FieldsSetModel:
    __slots__ = '__dict__', '__fields_set__'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture(scope='module', name='fs_model_serializer')
def fs_model_serializer_fixture():
    return SchemaSerializer(
        core_schema.model_schema(
            FieldsSetModel,
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(core_schema.int_schema()),
                    'b': core_schema.typed_dict_field(core_schema.int_schema()),
                    'c': core_schema.typed_dict_field(core_schema.int_schema()),
                    'd': core_schema.typed_dict_field(core_schema.int_schema()),
                    'e': core_schema.typed_dict_field(core_schema.int_schema()),
                    'f': core_schema.typed_dict_field(core_schema.int_schema()),
                    'g': core_schema.typed_dict_field(core_schema.int_schema()),
                    'h': core_schema.typed_dict_field(core_schema.int_schema()),
                }
            ),
        )
    )


@pytest.mark.benchmark(group='model-exclude-unset')
def test_model_exclude_unset_false(benchmark, fs_model_serializer):
    m = FieldsSetModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, __fields_set__={'a', 'b', 'c', 'd', 'e', 'f'})
    assert fs_model_serializer.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    assert fs_model_serializer.to_python(m, exclude_unset=True) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

    @benchmark
    def r():
        fs_model_serializer.to_python(m)


@pytest.mark.benchmark(group='model-exclude-unset')
def test_model_exclude_unset_true(benchmark, fs_model_serializer):
    m = FieldsSetModel(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, __fields_set__={'a', 'b', 'c', 'd', 'e', 'f'})
    assert fs_model_serializer.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
    assert fs_model_serializer.to_python(m, exclude_unset=True) == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

    @benchmark
    def r():
        fs_model_serializer.to_python(m, exclude_unset=True)


@skip_pydantic
@pytest.mark.benchmark(group='model-list-json')
def test_model_list_v1_json(benchmark):
    class PydanticModel(BaseModel):
        a: List[int]

    m = PydanticModel(a=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert m.json(exclude={'a': {1, 2}}) == '{"a": [0, 3, 4, 5, 6, 7, 8, 9]}'

    m_big = PydanticModel(a=list(range(1000)))
    j = m_big.json(exclude={'a': {1, 2}})
    assert j.startswith('{"a": [0, 3, 4')
    assert j.endswith('998, 999]}')

    @benchmark
    def r():
        m_big.json(exclude={'a': {1, 2}})


@pytest.mark.benchmark(group='model-list-json')
def test_model_list_core_json(benchmark):
    s = SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(
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
