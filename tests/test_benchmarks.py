import json
from typing import Dict, List, Optional

import pytest
from pydantic.main import BaseModel

from pydantic_core import SchemaValidator


class TestBenchmarkSimpleModel:
    class PydanticModel(BaseModel):
        name: str
        age: int
        friends: List[int]
        settings: Dict[str, float]

    class CoreModel:
        __slots__ = '__dict__', '__fields_set__'

    schema_validator = SchemaValidator(
        {
            'type': 'model-class',
            'class': CoreModel,
            'model': {
                'type': 'model',
                'fields': {
                    'name': {'type': 'str'},
                    'age': {'type': 'int'},
                    'friends': {'type': 'list', 'items': {'type': 'int'}},
                    'settings': {'type': 'dict', 'keys': {'type': 'str'}, 'values': {'type': 'float'}},
                },
            },
        }
    )

    data = {'name': 'John', 'age': 42, 'friends': list(range(200)), 'settings': {f'v_{i}': i / 2.0 for i in range(50)}}

    @pytest.mark.benchmark(group='simple model - python')
    def test_pydantic_python(self, benchmark):
        benchmark(self.PydanticModel.parse_obj, self.data)

    @pytest.mark.benchmark(group='simple model - python')
    def test_core_python(self, benchmark):
        benchmark(self.schema_validator.validate_python, self.data)

    @pytest.mark.benchmark(group='simple model - JSON')
    def test_pydantic_json(self, benchmark):
        json_data = json.dumps(self.data)

        @benchmark
        def pydantic_json():
            obj = json.loads(json_data)
            return self.PydanticModel.parse_obj(obj)

    @pytest.mark.benchmark(group='simple model - JSON')
    def test_core_json(self, benchmark):
        json_data = json.dumps(self.data)
        benchmark(self.schema_validator.validate_json, json_data)


bool_cases = [True, False, 0, 1, '0', '1', 'true', 'false', 'True', 'False']


@pytest.mark.benchmark(group='bool')
def test_bool_pydantic(benchmark):
    class PydanticModel(BaseModel):
        value: bool

    @benchmark
    def t():
        for case in bool_cases:
            PydanticModel(value=case)


@pytest.mark.benchmark(group='bool')
def test_bool_core(benchmark):
    schema_validator = SchemaValidator({'type': 'bool'})

    @benchmark
    def t():
        for case in bool_cases:
            schema_validator.validate_python(case)


small_class_data = {'name': 'John', 'age': 42}


@pytest.mark.benchmark(group='create small model')
def test_small_class_pydantic(benchmark):
    class PydanticModel(BaseModel):
        name: str
        age: int

    benchmark(PydanticModel.parse_obj, small_class_data)


@pytest.mark.benchmark(group='create small model')
def test_small_class_core_dict(benchmark):
    model_schema = {'type': 'model', 'fields': {'name': {'type': 'str'}, 'age': {'type': 'int'}}}
    dict_schema_validator = SchemaValidator(model_schema)
    benchmark(dict_schema_validator.validate_python, small_class_data)


@pytest.mark.benchmark(group='create small model')
def test_small_class_core_model(benchmark):
    class MyCoreModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        # these are here just as decoration
        name: str
        age: int

    model_schema_validator = SchemaValidator(
        {
            'type': 'model-class',
            'class': MyCoreModel,
            'model': {'type': 'model', 'fields': {'name': {'type': 'str'}, 'age': {'type': 'int'}}},
        }
    )
    benchmark(model_schema_validator.validate_python, small_class_data)


@pytest.fixture
def recursive_model_data():
    data = {'width': -1}

    _data = data
    for i in range(100):
        _data['branch'] = {'width': i}
        _data = _data['branch']
    return data


@pytest.mark.benchmark(group='recursive model')
def test_recursive_model_pydantic(recursive_model_data, benchmark):
    class PydanticBranch(BaseModel):
        width: int
        branch: Optional['PydanticBranch'] = None

    benchmark(PydanticBranch.parse_obj, recursive_model_data)


@pytest.mark.benchmark(group='recursive model')
def test_recursive_model_core(recursive_model_data, benchmark):
    class CoreBranch:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'

    v = SchemaValidator(
        {
            'type': 'recursive-container',
            'name': 'Branch',
            'schema': {
                'type': 'model-class',
                'class': CoreBranch,
                'model': {
                    'type': 'model',
                    'fields': {
                        'width': {'type': 'int'},
                        'branch': {
                            'type': 'optional',
                            'default': None,
                            'schema': {'type': 'recursive-ref', 'name': 'Branch'},
                        },
                    },
                },
            },
        }
    )
    benchmark(v.validate_python, recursive_model_data)
