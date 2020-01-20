import inspect
import sys

import pytest

from pydantic import BaseModel, ValidationError, validate_arguments
from pydantic.decorator import DecoratorSetupError, ValidatedFunction

skip_pre_38 = pytest.mark.skipif(sys.version_info < (3, 8), reason='testing >= 3.8 behaviour only')


def test_args():
    @validate_arguments
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(*[1, 2]) == '1, 2'
    assert foo(*(1, 2)) == '1, 2'
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

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, apple=3)

    assert exc_info.value.errors() == [
        {'loc': ('kwargs',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_wrap():
    @validate_arguments
    def foo(a: int, b: int):
        """This is the foo method."""
        return f'{a}, {b}'

    assert foo.__doc__ == 'This is the foo method.'
    assert foo.__name__ == 'foo'
    assert foo.__module__ == 'tests.test_decorator'
    assert foo.__qualname__ == 'test_wrap.<locals>.foo'
    assert isinstance(foo, ValidatedFunction)
    assert callable(foo.raw_function)
    assert foo.arg_mapping == {0: 'a', 1: 'b'}
    assert foo.args_field_name == 'args'
    assert foo.kwargs_field_name == 'kwargs'
    assert foo.positional_only_args == set()
    assert issubclass(foo.model, BaseModel)
    assert foo.model.__fields__.keys() == {'a', 'b'}
    # signature is slightly different on 3.6
    if sys.version_info < (3, 7):
        assert repr(inspect.signature(foo)) == '<Signature (a: int, b: int)>'


def test_kwargs():
    @validate_arguments
    def foo(*, a: int, b: int):
        return a + b

    assert foo.model.__fields__.keys() == {'a', 'b'}
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
def foo(a, b, /, c=None):
    return f'{a}, {b}, {c}'
"""
    )
    assert module.foo(1, 2) == '1, 2, None'
    assert module.foo(1, 2, 44) == '1, 2, 44'
    assert module.foo(1, 2, c=44) == '1, 2, 44'
    with pytest.raises(NotImplementedError):
        module.foo(1, b=2)


def test_args_name():
    @validate_arguments
    def foo(args: int, kwargs: int):
        return f'args={args!r}, kwargs={kwargs!r}'

    assert foo.model.__fields__.keys() == {'args', 'kwargs'}
    assert foo.args_field_name == 'var__args'
    assert foo.kwargs_field_name == 'var__kwargs'
    assert foo(1, 2) == 'args=1, kwargs=2'

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, apple=4)
    assert exc_info.value.errors() == [
        {'loc': ('var__kwargs',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, 3)
    assert exc_info.value.errors() == [
        {'loc': ('var__args',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_var__args():
    with pytest.raises(DecoratorSetupError, match='"var__args" and "var__kwargs" are not permitted as argument names'):

        @validate_arguments
        def foo(var__args: int):
            pass
