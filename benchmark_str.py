import sys
import timeit
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic_core._pydantic_core import check_str, check_list_str


class Foo(str, Enum):
    bar = "bar"
    baz = "baz"
    qux = "qux"


# print(repr(check_str(Foo.bar, None, 50, True, False, True)))
# s = check_str(b'hello ', 5, 50, True, False, True)
# print(f'rust: {s!r}')
# s = check_str(Decimal('123'), 5, 50, True, False, True)
# print(f'rust: {s!r}')
s = check_str(b'hello ', 5, 50, True, False, True)
print(f'rust: {s!r}')

steps = 10_000
t = timeit.timeit(
    "check_str(b'hello ', 2, 50, True, False, True)",
    globals=globals(),
    number=steps,
)
print(f'rust check_str: {t / steps * 1_000_000:.2f}µs')

choices = [
    'this is a string',
    'this is another string',
    'this is a third string',
    b'hello ',
    123,
    123.456,
    Decimal('321.123'),
]

debug(check_list_str(choices, 2, 50, True, False, True))

t = timeit.timeit(
    'check_list_str(choices * 100, 2, 50, True, False, True)',
    globals=globals(),
    number=steps,
)
print(f'rust check_list_str: {t / steps * 1_000_000:.2f}µs')


def py_str_validate(v):
    if isinstance(v, str):
        return v
    elif isinstance(v, bytes):
        return v.decode()
    elif isinstance(v, (int, float, Decimal)):
        return str(v)
    else:
        raise TypeError(f'{type(v)} is not a string')


def py_str_check(
    s,
    min_length: Optional[int],
    max_length: Optional[int],
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
):
    s = py_str_validate(s)

    if min_length is not None and len(s) < min_length:
        raise ValueError(f'String is too short (min length: {min_length})')
    if max_length is not None and len(s) > max_length:
        raise ValueError(f'String is too long (max length: {max_length})')

    if strip_whitespace:
        s = s.strip()

    if to_lower:
        return s.lower()
    if to_upper:
        return s.upper()
    else:
        return s


debug(py_str_check('hello ', 5, 50, True, False, True))

t = timeit.timeit(
    "py_str_check(b'hello ', 5, 50, True, False, True)",
    globals=globals(),
    number=steps,
)
print(f'py_str_check: {t / steps * 1_000_000:.2f}µs')


def py_check_list_str(
    items,
    min_length: Optional[int],
    max_length: Optional[int],
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
):
    new_items = []
    for item in items:
        new_items.append(py_str_check(item, min_length, max_length, strip_whitespace, to_lower, to_upper))
    return new_items


debug(py_check_list_str(choices, 2, 50, True, False, True))

t = timeit.timeit(
    'py_check_list_str(choices * 100, 2, 50, True, False, True)',
    globals=globals(),
    number=steps,
)
print(f'py_check_list_str: {t / steps * 1_000_000:.2f}µs')
