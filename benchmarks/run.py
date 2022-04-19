#!/usr/bin/env python3
import timeit
from typing import List, Dict

# import ujson as json
import json

from devtools import debug


def benchmark_simple_validation(from_json: bool = False):
    from pydantic import BaseModel
    from pydantic_core import SchemaValidator

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

    benchmark_functions = []

    def benchmark(f):
        benchmark_functions.append(f)
        return f

    if from_json:
        data = json.dumps(data)

        @benchmark
        def pydantic_json(d):
            obj = json.loads(d)
            return PydanticModel.parse_obj(obj)

        @benchmark
        def core_json(d):
            schema_validator.validate_json(d)
            # output, fields_set = schema_validator.validate_json(d)
            # return output

        # @benchmark
        # def core_json_external(d):
        #     obj = json.loads(d)
        #     output, fields_set = schema_validator.validate_python(obj)
        #     return output

    else:
        @benchmark
        def pydantic_py(d):
            return PydanticModel.parse_obj(d)

        @benchmark
        def core_py(d):
            output, fields_set = schema_validator.validate_python(d)
            return output

    reference_result = None
    steps = 1_000

    for func in benchmark_functions:
        print(f'{func.__name__}:')
        result = func(data)
        # debug(result)
        # if reference_result:
        #     assert reference_result == result
        # reference_result = result

        t = timeit.timeit(
            'func(data)',
            globals={'func': func, 'data': data},
            number=steps,
        )
        print(f'    {display_time(t / steps)}\n')


def display_time(seconds: float):
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
