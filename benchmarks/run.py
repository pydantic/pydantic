#!/usr/bin/env python3
import timeit
from typing import List, Dict

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

    schema_validator = SchemaValidator({
        'model_name': 'TestModel',
        'type': 'model',
        'fields': {
            'name': {
                'type': 'str',
            },
            'age': {
                'type': 'int',
            },
            'friends': {
                'type': 'list',
                'items': {
                    'type': 'int',
                },
            },
            'settings': {
                'type': 'dict',
                'keys': {
                    'type': 'str',
                },
                'values': {
                    'type': 'float',
                }
            }
        },
    })

    data = {'name': 'John', 'age': 42, 'friends': list(range(200)), 'settings': {f'v_{i}': i / 2.0 for i in range(50)}}

    if from_json:
        data = json.dumps(data)

        def pydantic(d):
            obj = json.loads(d)
            return PydanticModel.parse_obj(obj)

        def pydantic_core(d):
            output, fields_set = schema_validator.validate_json(d)
            return output

        _run_benchmarks('simple model from JSON', [pydantic, pydantic_core], [data])
    else:
        def pydantic(d):
            return PydanticModel.parse_obj(d)

        def pydantic_core(d):
            output, fields_set = schema_validator.validate_python(d)
            return output

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

    model_schema = {
        'type': 'model',
        'fields': {
            'name': {
                'type': 'str',
            },
            'age': {
                'type': 'int',
            }
        },
    }
    dict_schema_validator = SchemaValidator(model_schema)

    class MyCoreModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        # these are here just as decoration
        name: str
        age: int

    model_schema_validator = SchemaValidator({
        'type': 'model-class',
        'class': MyCoreModel,
        'model': model_schema
    })

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


def _run_benchmarks(name: str, benchmark_functions: list, input_values: list, steps: int = 1_000):
    reference_result = None

    print(f'\n#################\n{name}')
    for func in benchmark_functions:
        print(f'{func.__name__}:')
        outputs = [func(data) for data in input_values]
        result = list(zip(input_values, outputs))
        # debug(result)
        if reference_result:
            assert reference_result == result, (func.__name__, reference_result, result)
        reference_result = result

        t = timeit.timeit(
            '[func(data) for data in input_values]',
            globals={'func': func, 'input_values': input_values},
            number=steps,
        )
        print(f'    {_display_time(t / steps)}')


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
