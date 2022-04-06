import timeit
from decimal import Decimal
from enum import Enum

from devtools import debug

import plain
from pydantic_core import _pydantic_core as rust

implementations = plain, rust


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
]

data = {
    'str': 'this is a string',
    'list': choices,
    'dict': {'foo': 'bar', 'baz': choices},
}

old_result = None
steps = 1_000

for impl in implementations:
    print(f'\n{impl.__name__}:')
    result = impl.validate_str_recursive(data, None, 50, True, False, True)
    # debug(result)
    if old_result:
        assert result == old_result
    old_result = result

    big_data = [data] * 100
    t = timeit.timeit(
        'impl.validate_str_recursive(big_data, None, 50, True, False, True)',
        globals=globals(),
        number=steps,
    )
    print(f'    validate_str_recursive: {t / steps * 1_000_000:.2f}µs')
