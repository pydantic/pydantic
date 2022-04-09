import timeit
from typing import List, Dict

from devtools import debug


def benchmark_simple_validation():
    from pydantic import BaseModel
    from pydantic_core import SchemaValidator

    class PydanticModel(BaseModel):
        name: str
        age: int
        friends: List[int]
        settings: Dict[str, float]

    schema_validator = SchemaValidator({
        'type': 'model',
        'fields': {
            'name': {
                'type': 'str',
                'required': True,
            },
            'age': {
                'type': 'int',
            },
            'friends': {
                'type': 'list',
                'items': {
                    'type': 'int',
                },
                'required': True,
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

    data = {'name': 'John', 'age': 42, 'friends': list(range(20)), 'settings': {f'v_{i}': i / 2.0 for i in range(50)}}

    def pydantic(d):
        return PydanticModel.parse_obj(d)

    def pydantic_core(d):
        return schema_validator.validate(d)

    impls = pydantic, pydantic_core
    old_result = None
    steps = 1_000

    for impl in impls:
        print(f'{impl.__name__}:')
        result = impl(data)
        # debug(result)
        if old_result:
            assert result == old_result
        old_result = result

        t = timeit.timeit(
            'impl(data)',
            globals={'impl': impl, 'data': data},
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
