import sys

import pytest

from pydantic import ValidationError, validate_arguments

skip_pre_38 = pytest.mark.skipif(sys.version_info < (3, 8), reason='testing >= 3.8 behaviour only')


def test_args():
    @validate_arguments
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(*[1, 2]) == '1, 2'
    assert foo(*[1], 2) == '1, 2'

    with pytest.raises(ValidationError) as exc_info:
        foo()

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')

    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_kwargs():
    @validate_arguments
    def foo(*, a: int, b: int):
        return a + b

    assert foo(a=1, b=3) == 4

    with pytest.raises(ValidationError) as exc_info:
        foo(a=1, b='x')

    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('args',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_untyped():
    @validate_arguments
    def foo(a, b, c='x', *, d='y'):
        return ', '.join(str(arg) for arg in [a, b, c, d])

    assert foo(1, 2) == '1, 2, x, y'
    assert foo(1, {'x': 2}, c='3', d='4') == "1, {'x': 2}, 3, 4"


def test_var_args_kwargs():
    @validate_arguments
    def foo(a, b, *args, d=3, **kwargs):
        return f'a={a!r}, b={b!r}, args={args!r}, d={d!r}, kwargs={kwargs!r}'

    assert foo(1, 2) == 'a=1, b=2, args=(), d=3, kwargs={}'
    assert foo(1, 2, 3, d=4) == 'a=1, b=2, args=(3,), d=4, kwargs={}'
    assert foo(*[1, 2, 3], d=4) == 'a=1, b=2, args=(3,), d=4, kwargs={}'
    assert foo(1, 2, 3, e=10) == "a=1, b=2, args=(3,), d=3, kwargs={'e': 10}"


@skip_pre_38
def test_position_only(create_module):
    module = create_module(
        """
from pydantic import validate_arguments

@validate_arguments
def foo(a, b, /):
    return f'{a}, {b}'
"""
    )
    assert module.foo(1, 2) == '1, 2'
    with pytest.raises(NotImplementedError):
        module.foo(1, b=2)
