import json
from typing import Dict, List, Optional, Set

import pytest

from pydantic_core import SchemaValidator

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None


pytestmark = pytest.mark.skipif(BaseModel is None, reason='pydantic not installed; tests fail on 3.7')


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
    def core_validator(self):
        class CoreModel:
            __slots__ = '__dict__', '__fields_set__'

        return SchemaValidator(
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
    def test_pyd_python(self, pydantic_model, benchmark):
        benchmark(pydantic_model.parse_obj, self.data)

    @pytest.mark.benchmark(group='simple model - python')
    def test_core_python(self, core_validator, benchmark):
        benchmark(core_validator.validate_python, self.data)

    @pytest.mark.benchmark(group='simple model - JSON')
    def test_pyd_json(self, pydantic_model, benchmark):
        json_data = json.dumps(self.data)

        @benchmark
        def pydantic_json():
            obj = json.loads(json_data)
            return pydantic_model.parse_obj(obj)

    @pytest.mark.benchmark(group='simple model - JSON')
    def test_core_json(self, core_validator, benchmark):
        json_data = json.dumps(self.data)
        benchmark(core_validator.validate_json, json_data)


bool_cases = [True, False, 0, 1, '0', '1', 'true', 'false', 'True', 'False']


@pytest.mark.benchmark(group='bool')
def test_bool_pyd(benchmark):
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
def test_small_class_pyd(benchmark):
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
def test_recursive_model_pyd(recursive_model_data, benchmark):
    class PydanticBranch(BaseModel):
        width: int
        branch: Optional['PydanticBranch'] = None  # noqa: F821

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


@pytest.mark.benchmark(group='list of dict models')
def test_list_of_dict_models_pyd(benchmark):
    class PydanticBranch(BaseModel):
        width: int

    class PydanticRoot(BaseModel):
        __root__: List[PydanticBranch]

    data = [{'width': i} for i in range(100)]
    benchmark(PydanticRoot.parse_obj, data)


@pytest.mark.benchmark(group='list of dict models')
def test_list_of_dict_models_core(benchmark):
    v = SchemaValidator(
        {'type': 'list', 'name': 'Branch', 'items': {'type': 'model', 'fields': {'width': {'type': 'int'}}}}
    )

    data = [{'width': i} for i in range(100)]
    benchmark(v.validate_python, data)


list_of_ints_data = ([i for i in range(1000)], [str(i) for i in range(1000)])


@pytest.mark.benchmark(group='list of ints')
def test_list_of_ints_pyd_py(benchmark):
    class PydanticTree(BaseModel):
        __root__: List[int]

    @benchmark
    def t():
        PydanticTree.parse_obj(list_of_ints_data[0])
        PydanticTree.parse_obj(list_of_ints_data[1])


@pytest.mark.benchmark(group='list of ints')
def test_list_of_ints_core_py(benchmark):
    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}})

    @benchmark
    def t():
        v.validate_python(list_of_ints_data[0])
        v.validate_python(list_of_ints_data[1])


@pytest.mark.benchmark(group='list of ints')
def test_list_of_ints_pyd_json(benchmark):
    class PydanticTree(BaseModel):
        __root__: List[int]

    json_data = [json.dumps(d) for d in list_of_ints_data]

    @benchmark
    def t():
        PydanticTree.parse_obj(json.loads(json_data[0]))
        PydanticTree.parse_obj(json.loads(json_data[1]))


@pytest.mark.benchmark(group='list of ints')
def test_list_of_ints_core_json(benchmark):
    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}})

    json_data = [json.dumps(d) for d in list_of_ints_data]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


set_of_ints_data = ({i for i in range(1000)}, {str(i) for i in range(1000)})


@pytest.mark.benchmark(group='set of ints')
def test_set_of_ints_pyd(benchmark):
    class PydanticTree(BaseModel):
        __root__: Set[int]

    @benchmark
    def t():
        PydanticTree.parse_obj(set_of_ints_data[0])
        PydanticTree.parse_obj(set_of_ints_data[1])


@pytest.mark.benchmark(group='set of ints')
def test_set_of_ints_core(benchmark):
    v = SchemaValidator({'type': 'set', 'items': {'type': 'int'}})

    @benchmark
    def t():
        v.validate_python(set_of_ints_data[0])
        v.validate_python(set_of_ints_data[1])


@pytest.mark.benchmark(group='set of ints')
def test_set_of_ints_pyd_json(benchmark):
    class PydanticTree(BaseModel):
        __root__: Set[int]

    json_data = [json.dumps(list(d)) for d in set_of_ints_data]

    @benchmark
    def t():
        PydanticTree.parse_obj(json.loads(json_data[0]))
        PydanticTree.parse_obj(json.loads(json_data[1]))


@pytest.mark.benchmark(group='set of ints')
def test_set_of_ints_core_json(benchmark):
    v = SchemaValidator({'type': 'set', 'items': {'type': 'int'}})

    json_data = [json.dumps(list(d)) for d in set_of_ints_data]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


dict_of_ints_data = ({i: i for i in range(1000)}, {i: str(i) for i in range(1000)})


@pytest.mark.benchmark(group='dict of ints')
def test_dict_of_ints_pyd(benchmark):
    class PydanticTree(BaseModel):
        __root__: Dict[str, int]

    @benchmark
    def t():
        PydanticTree.parse_obj(dict_of_ints_data[0])
        PydanticTree.parse_obj(dict_of_ints_data[1])


@pytest.mark.benchmark(group='dict of ints')
def test_dict_of_ints_core(benchmark):
    v = SchemaValidator({'type': 'dict', 'keys': 'str', 'values': 'int'})

    @benchmark
    def t():
        v.validate_python(dict_of_ints_data[0])
        v.validate_python(dict_of_ints_data[1])


@pytest.mark.benchmark(group='dict of ints')
def test_dict_of_ints_pyd_json(benchmark):
    class PydanticTree(BaseModel):
        __root__: Dict[str, int]

    json_data = [json.dumps(d) for d in dict_of_ints_data]

    @benchmark
    def t():
        PydanticTree.parse_obj(json.loads(json_data[0]))
        PydanticTree.parse_obj(json.loads(json_data[1]))


@pytest.mark.benchmark(group='dict of ints')
def test_dict_of_ints_core_json(benchmark):
    v = SchemaValidator({'type': 'dict', 'keys': 'str', 'values': 'int'})

    json_data = [json.dumps(d) for d in dict_of_ints_data]

    @benchmark
    def t():
        v.validate_json(json_data[0])
        v.validate_json(json_data[1])


many_models_data = [{'age': i} for i in range(1000)]


@pytest.mark.benchmark(group='many models')
def test_many_models_pyd(benchmark):
    class SimpleMode(BaseModel):
        age: int

    class PydanticModel(BaseModel):
        __root__: List[SimpleMode]

    benchmark(PydanticModel.parse_obj, many_models_data)


@pytest.mark.benchmark(group='many models')
def test_many_models_core_dict(benchmark):
    model_schema = {'type': 'list', 'items': {'type': 'model', 'fields': {'age': 'int'}}}
    v = SchemaValidator(model_schema)
    benchmark(v.validate_python, many_models_data)


@pytest.mark.benchmark(group='many models')
def test_many_models_core_model(benchmark):
    class MyCoreModel:
        __slots__ = '__dict__', '__fields_set__'

    v = SchemaValidator(
        {
            'type': 'list',
            'items': {
                'type': 'model-class',
                'class': MyCoreModel,
                'model': {'type': 'model', 'fields': {'age': 'int'}},
            },
        }
    )
    benchmark(v.validate_python, many_models_data)
