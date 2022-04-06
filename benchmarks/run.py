import timeit
from decimal import Decimal
from enum import Enum
from statistics import mean

from devtools import debug


def benchmark_str_validation():
    import plain_validators
    from pydantic_core import _pydantic_core as rust

    impls = plain_validators, rust

    class Foo(str, Enum):
        bar = 'bar'
        baz = 'baz'
        qux = 'qux'

    choices = [
        'this is a string',
        'this is another string',
        'this is a third string',
        b'hello ',
        Foo.bar,
        123,
        123.456,
        Decimal('321.123'),
        [1, 2, 3,  'this is a string', b'hello ', Foo.bar, 123, 123.456, Decimal('321.123')],
        {'a': 'this is a string', 'b': 123, 'c': Foo.baz},
        # object(),
    ]

    data = {
        'str': 'this is a string',
        'list': choices,
        'dict': {'foo': 'bar', 'baz': choices},
    }

    old_result = None
    steps = 1_000

    for impl in impls:
        print(f'{impl.__name__} validate_str_recursive:')
        result = impl.validate_str_recursive(data, None, 50, True, False, True)
        # debug(result)
        if old_result:
            assert result == old_result
        old_result = result

        big_data = [data] * 100
        t = timeit.timeit(
            'impl.validate_str_recursive(big_data, None, 50, True, False, True)',
            globals={'impl': impl, 'big_data': big_data},
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
    benchmark_str_validation()
