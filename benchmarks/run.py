#!/usr/bin/env python3
import timeit
from typing import List, Dict, Optional, Set

# import ujson as json
import json

from devtools import debug

from pydantic import BaseModel
from pydantic_core import SchemaValidator


def benchmark_simple_validation(from_json: bool = False):
    class PydanticModel(BaseModel):
        name: str
        age: int
        friends: List[int]
        settings: Dict[str, float]

    class MyCoreModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        name: str
        age: int
        friends: List[int]
        settings: Dict[str, float]

    schema_validator = SchemaValidator(
        {
            'type': 'model-class',
            'class': MyCoreModel,
            'model': {
                'type': 'model',
                'fields': {
                    'name': {'type': 'str'},
                    'age': {'type': 'int'},
                    'friends': {'type': 'list', 'items': {'type': 'int'}},
                    'settings': {'type': 'dict', 'keys': {'type': 'str'}, 'values': {'type': 'float'}},
                },
            }
        }
    )

    data = {'name': 'John', 'age': 42, 'friends': list(range(200)), 'settings': {f'v_{i}': i / 2.0 for i in range(50)}}

    if from_json:
        data = json.dumps(data)

        def pydantic(d):
            obj = json.loads(d)
            return PydanticModel.parse_obj(obj)

        def pydantic_core(d):
            output = schema_validator.validate_json(d)
            return output.__dict__

        _run_benchmarks('simple model from JSON', [pydantic, pydantic_core], [data])
    else:

        def pydantic(d):
            return PydanticModel.parse_obj(d)

        def pydantic_core(d):
            output = schema_validator.validate_python(d)
            return output.__dict__

        _run_benchmarks('simple model from py', [pydantic, pydantic_core], [data])


def benchmark_bool():
    class PydanticModel(BaseModel):
        value: bool

    schema_validator = SchemaValidator({'type': 'bool'})

    def pydantic(d):
        m = PydanticModel(value=d)
        return m.value

    def pydantic_core(d):
        return schema_validator.validate_python(d)

    data = [True, False, 0, 1, 'true', 'True', 'false', 'False', 'yes', 'no']

    _run_benchmarks('bool', [pydantic, pydantic_core], data, steps=50_000)


def benchmark_model_create():
    class PydanticModel(BaseModel):
        name: str
        age: int

    model_schema = {'type': 'model', 'fields': {'name': {'type': 'str'}, 'age': {'type': 'int'}}}
    dict_schema_validator = SchemaValidator(model_schema)

    class MyCoreModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        # these are here just as decoration
        name: str
        age: int

    model_schema_validator = SchemaValidator({'type': 'model-class', 'class': MyCoreModel, 'model': model_schema})

    def pydantic(d):
        m = PydanticModel(**d)
        return m.__dict__

    def pydantic_core_dict(d):
        output, fields_set = dict_schema_validator.validate_python(d)
        return output

    def pydantic_core_model(d):
        m = model_schema_validator.validate_python(d)
        return m.__dict__

    data = {'name': 'John', 'age': 42}

    _run_benchmarks('model_create', [pydantic, pydantic_core_dict, pydantic_core_model], [data], steps=10_000)


def benchmark_recursive_model():
    class PydanticBranch(BaseModel):
        width: int
        branch: Optional['PydanticBranch'] = None

    class CoreBranch:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        # these are here just as decoration
        width: int
        branch: Optional['CoreBranch']

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

    # we can't compare .__dict__ here since it contains classes that won't be equal

    def pydantic(d):
        m = PydanticBranch(**d)
        return m.__fields_set__

    def pydantic_core(d):
        m = v.validate_python(d)
        return m.__fields_set__

    data = {'width': -1}

    _data = data
    for i in range(100):
        _data['branch'] = {'width': i}
        _data = _data['branch']

    _run_benchmarks('benchmark_recursive_model', [pydantic, pydantic_core], [data])


def benchmark_list_of_dict_models():
    class PydanticBranch(BaseModel):
        width: int

    class PydanticTree(BaseModel):
        __root__: List[PydanticBranch]

    v = SchemaValidator(
        {
            'type': 'list',
            'name': 'Branch',
            'items': {
                'type': 'model',
                'fields': {
                    'width': {'type': 'int'},
                },
            },
        }
    )
    # debug(v)

    def pydantic(d):
        m = PydanticTree.parse_obj(d)
        return [m.dict() for m in m.__root__]

    def pydantic_core(d):
        return [d for d, f in v.validate_python(d)]

    data = [{'width': i} for i in range(100)]

    _run_benchmarks('benchmark_list_of_dict_models', [pydantic, pydantic_core], [data])


def benchmark_list_of_ints(json_data):
    class PydanticTree(BaseModel):
        __root__: List[int]

    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}})
    data = [
        [i for i in range(1000)],
        [str(i) for i in range(1000)],
    ]
    if json_data:
        data = [json.dumps(d) for d in data]

        def pydantic(d):
            obj = json.loads(d)
            return PydanticTree.parse_obj(obj).__root__

        def pydantic_core(d):
            return v.validate_json(d)
    else:
        def pydantic(d):
            return PydanticTree.parse_obj(d).__root__

        def pydantic_core(d):
            return v.validate_python(d)

    _run_benchmarks(f'benchmark_list_of_ints_{"json" if json_data else "py"}', [pydantic, pydantic_core], data)


def benchmark_set_of_ints(json_data):
    class PydanticTree(BaseModel):
        __root__: Set[int]

    v = SchemaValidator({'type': 'set', 'items': {'type': 'int'}})
    data = [
        {i for i in range(1000)},
        {str(i) for i in range(1000)},
    ]
    if json_data:
        data = [json.dumps(list(d)) for d in data]

        def pydantic(d):
            obj = json.loads(d)
            return PydanticTree.parse_obj(obj).__root__

        def pydantic_core(d):
            return v.validate_json(d)
    else:
        def pydantic(d):
            return PydanticTree.parse_obj(d).__root__

        def pydantic_core(d):
            return v.validate_python(d)

    _run_benchmarks(f'benchmark_set_of_ints_{"json" if json_data else "py"}', [pydantic, pydantic_core], data)


def _run_benchmarks(name: str, benchmark_functions: list, input_values: list, steps: int = 1_000):
    reference_result = None
    reference_speed = None

    print(f'\n#################\n{name}')
    for func in benchmark_functions:
        print(f'{func.__name__}:')
        outputs = [func(data) for data in input_values]
        result = list(zip(input_values, outputs))
        # debug(result)
        if reference_result:
            assert reference_result == result, debug.format(result, reference_result, result)
        reference_result = result

        t = timeit.timeit(
            '[func(data) for data in input_values]', globals={'func': func, 'input_values': input_values}, number=steps
        )
        speed = t / steps
        if reference_speed is None:
            print(f'    {_display_time(speed)}')
            reference_speed = speed
        else:
            print(f'    {_display_time(speed)} {reference_speed / speed:.2f}x')


def _display_time(seconds: float):
    ns = seconds * 1_000_000_000
    if ns < 1000:
        return f'{ns:.2f}ns'
    micros = ns / 1000
    if micros < 1000:
        return f'{micros:.2f}µs'
    millis = micros / 1000
    if millis < 1000:
        return f'{millis:.2f}ms'

    return f'{seconds:.2f}s'


if __name__ == '__main__':
    benchmark_simple_validation()
    benchmark_simple_validation(from_json=True)
    benchmark_bool()
    benchmark_model_create()
    benchmark_recursive_model()
    benchmark_list_of_dict_models()
    benchmark_list_of_ints(True)
    benchmark_list_of_ints(False)
    benchmark_set_of_ints(True)
    benchmark_set_of_ints(False)
