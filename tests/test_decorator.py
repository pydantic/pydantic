import asyncio
import inspect
import sys
from pathlib import Path
from typing import List

import pytest

from pydantic import BaseModel, ValidationError, validate_arguments
from pydantic.decorator import ValidatedFunction
from pydantic.errors import ConfigError

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
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, 3)

    assert exc_info.value.errors() == [
        {'loc': ('args',), 'msg': '2 positional arguments expected but 3 given', 'type': 'type_error'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, apple=3)

    assert exc_info.value.errors() == [
        {'loc': ('kwargs',), 'msg': "unexpected keyword argument: 'apple'", 'type': 'type_error'}
    ]


def test_wrap():
    @validate_arguments
    def foo_bar(a: int, b: int):
        """This is the foo_bar method."""
        return f'{a}, {b}'

    assert foo_bar.__doc__ == 'This is the foo_bar method.'
    assert foo_bar.__name__ == 'foo_bar'
    assert foo_bar.__module__ == 'tests.test_decorator'
    assert foo_bar.__qualname__ == 'test_wrap.<locals>.foo_bar'
    assert isinstance(foo_bar.vd, ValidatedFunction)
    assert callable(foo_bar.raw_function)
    assert foo_bar.vd.arg_mapping == {0: 'a', 1: 'b'}
    assert foo_bar.vd.positional_only_args == set()
    assert issubclass(foo_bar.model, BaseModel)
    assert foo_bar.model.__fields__.keys() == {'a', 'b', 'args', 'kwargs'}
    assert foo_bar.model.__name__ == 'FooBar'
    assert foo_bar.model.schema()['title'] == 'FooBar'
    # signature is slightly different on 3.6
    if sys.version_info >= (3, 7):
        assert repr(inspect.signature(foo_bar)) == '<Signature (a: int, b: int)>'


def test_kwargs():
    @validate_arguments
    def foo(*, a: int, b: int):
        return a + b

    assert foo.model.__fields__.keys() == {'a', 'b', 'args', 'kwargs'}
    assert foo(a=1, b=3) == 4

    with pytest.raises(ValidationError) as exc_info:
        foo(a=1, b='x')

    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('args',), 'msg': '0 positional arguments expected but 2 given', 'type': 'type_error'},
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
def test_positional_only(create_module):
    module = create_module(
        # language=Python
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
    with pytest.raises(ValidationError) as exc_info:
        module.foo(1, b=2)
    assert exc_info.value.errors() == [
        {
            'loc': ('v__positional_only',),
            'msg': "positional-only argument passed as keyword argument: 'b'",
            'type': 'type_error',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        module.foo(a=1, b=2)
    assert exc_info.value.errors() == [
        {
            'loc': ('v__positional_only',),
            'msg': "positional-only arguments passed as keyword arguments: 'a', 'b'",
            'type': 'type_error',
        }
    ]


def test_args_name():
    @validate_arguments
    def foo(args: int, kwargs: int):
        return f'args={args!r}, kwargs={kwargs!r}'

    assert foo.model.__fields__.keys() == {'args', 'kwargs', 'v__args', 'v__kwargs'}
    assert foo(1, 2) == 'args=1, kwargs=2'

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, apple=4)
    assert exc_info.value.errors() == [
        {'loc': ('v__kwargs',), 'msg': "unexpected keyword argument: 'apple'", 'type': 'type_error'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, apple=4, banana=5)
    assert exc_info.value.errors() == [
        {'loc': ('v__kwargs',), 'msg': "unexpected keyword arguments: 'apple', 'banana'", 'type': 'type_error'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, 3)
    assert exc_info.value.errors() == [
        {'loc': ('v__args',), 'msg': '2 positional arguments expected but 3 given', 'type': 'type_error'}
    ]


def test_v_args():
    with pytest.raises(ConfigError, match='"v__args", "v__kwargs" and "v__positional_only" are not permitted'):

        @validate_arguments
        def foo(v__args: int):
            pass


def test_async():
    @validate_arguments
    async def foo(a, b):
        return f'a={a} b={b}'

    async def run():
        v = await foo(1, 2)
        assert v == 'a=1 b=2'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    with pytest.raises(ValidationError) as exc_info:
        loop.run_until_complete(foo('x'))
    assert exc_info.value.errors() == [{'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_string_annotation():
    @validate_arguments
    def foo(a: 'List[int]', b: 'Path'):
        return f'a={a!r} b={b!r}'

    assert foo([1, 2, 3], '/')

    with pytest.raises(ValidationError) as exc_info:
        foo(['x'])
    assert exc_info.value.errors() == [
        {'loc': ('a', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_item_method():
    class X:
        def __init__(self, v):
            self.v = v

        @validate_arguments
        def foo(self, a: int, b: int):
            assert self.v == a
            return f'{a}, {b}'

    x = X(4)
    assert x.foo(4, 2) == '4, 2'
    assert x.foo(*[4, 2]) == '4, 2'

    with pytest.raises(ValidationError) as exc_info:
        x.foo()

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_class_method():
    class X:
        @classmethod
        @validate_arguments
        def foo(cls, a: int, b: int):
            assert cls == X
            return f'{a}, {b}'

    x = X()
    assert x.foo(4, 2) == '4, 2'
    assert x.foo(*[4, 2]) == '4, 2'

    with pytest.raises(ValidationError) as exc_info:
        x.foo()

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_config_title():
    @validate_arguments(config=dict(title='Testing'))
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo.model.schema()['title'] == 'Testing'


def test_config_title_cls():
    class Config:
        title = 'Testing'

    @validate_arguments(config=Config)
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo.model.schema()['title'] == 'Testing'


def test_config_fields():
    with pytest.raises(ConfigError, match='Setting the "fields" and "alias_generator" property on custom Config for @'):

        @validate_arguments(config=dict(fields={'b': 'bang'}))
        def foo(a: int, b: int):
            return f'{a}, {b}'


def test_config_arbitrary_types_allowed():
    class EggBox:
        def __str__(self) -> str:
            return 'EggBox()'

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def foo(a: int, b: EggBox):
        return f'{a}, {b}'

    assert foo(1, EggBox()) == '1, EggBox()'
    with pytest.raises(ValidationError) as exc_info:
        assert foo(1, 2) == '1, 2'

    assert exc_info.value.errors() == [
        {
            'loc': ('b',),
            'msg': 'instance of EggBox expected',
            'type': 'type_error.arbitrary_type',
            'ctx': {'expected_arbitrary_type': 'EggBox'},
        },
    ]


def test_validate(mocker):
    stub = mocker.stub(name='on_something_stub')

    @validate_arguments
    def func(s: str, count: int, *, separator: bytes = b''):
        stub(s, count, separator)

    func.validate('qwe', 2)
    with pytest.raises(ValidationError):
        func.validate(['qwe'], 2)

    stub.assert_not_called()
