import asyncio
import inspect
from pathlib import Path
from typing import List

import pytest
from dirty_equals import IsInstance
from typing_extensions import Annotated

from pydantic import BaseModel, Field, PydanticDeprecatedSince20, ValidationError
from pydantic.deprecated.decorator import ValidatedFunction
from pydantic.deprecated.decorator import validate_arguments as validate_arguments_deprecated
from pydantic.errors import PydanticUserError


def validate_arguments(*args, **kwargs):
    with pytest.warns(
        PydanticDeprecatedSince20, match='^The `validate_arguments` method is deprecated; use `validate_call`'
    ):
        return validate_arguments_deprecated(*args, **kwargs)


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
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'x',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]

    with pytest.raises(TypeError, match='2 positional arguments expected but 3 given'):
        foo(1, 2, 3)

    with pytest.raises(TypeError, match="unexpected keyword argument: 'apple'"):
        foo(1, 2, apple=3)

    with pytest.raises(TypeError, match="multiple values for argument: 'a'"):
        foo(1, 2, a=3)

    with pytest.raises(TypeError, match="multiple values for arguments: 'a', 'b'"):
        foo(1, 2, a=3, b=4)


def test_wrap():
    @validate_arguments
    def foo_bar(a: int, b: int):
        """This is the foo_bar method."""
        return f'{a}, {b}'

    assert foo_bar.__doc__ == 'This is the foo_bar method.'
    assert foo_bar.__name__ == 'foo_bar'
    assert foo_bar.__module__ == 'tests.test_deprecated_validate_arguments'
    assert foo_bar.__qualname__ == 'test_wrap.<locals>.foo_bar'
    assert isinstance(foo_bar.vd, ValidatedFunction)
    assert callable(foo_bar.raw_function)
    assert foo_bar.vd.arg_mapping == {0: 'a', 1: 'b'}
    assert foo_bar.vd.positional_only_args == set()
    assert issubclass(foo_bar.model, BaseModel)
    assert foo_bar.model.model_fields.keys() == {'a', 'b', 'args', 'kwargs', 'v__duplicate_kwargs'}
    assert foo_bar.model.__name__ == 'FooBar'
    assert foo_bar.model.model_json_schema()['title'] == 'FooBar'
    assert repr(inspect.signature(foo_bar)) == '<Signature (a: int, b: int)>'


def test_kwargs():
    @validate_arguments
    def foo(*, a: int, b: int):
        return a + b

    assert foo.model.model_fields.keys() == {'a', 'b', 'args', 'kwargs'}
    assert foo(a=1, b=3) == 4

    with pytest.raises(ValidationError) as exc_info:
        foo(a=1, b='x')

    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'x',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]

    with pytest.raises(TypeError, match='0 positional arguments expected but 2 given'):
        foo(1, 'x')


def test_untyped():
    @validate_arguments
    def foo(a, b, c='x', *, d='y'):
        return ', '.join(str(arg) for arg in [a, b, c, d])

    assert foo(1, 2) == '1, 2, x, y'
    assert foo(1, {'x': 2}, c='3', d='4') == "1, {'x': 2}, 3, 4"


@pytest.mark.parametrize('validated', (True, False))
def test_var_args_kwargs(validated):
    def foo(a, b, *args, d=3, **kwargs):
        return f'a={a!r}, b={b!r}, args={args!r}, d={d!r}, kwargs={kwargs!r}'

    if validated:
        foo = validate_arguments(foo)

    assert foo(1, 2) == 'a=1, b=2, args=(), d=3, kwargs={}'
    assert foo(1, 2, 3, d=4) == 'a=1, b=2, args=(3,), d=4, kwargs={}'
    assert foo(*[1, 2, 3], d=4) == 'a=1, b=2, args=(3,), d=4, kwargs={}'
    assert foo(1, 2, args=(10, 11)) == "a=1, b=2, args=(), d=3, kwargs={'args': (10, 11)}"
    assert foo(1, 2, 3, args=(10, 11)) == "a=1, b=2, args=(3,), d=3, kwargs={'args': (10, 11)}"
    assert foo(1, 2, 3, e=10) == "a=1, b=2, args=(3,), d=3, kwargs={'e': 10}"
    assert foo(1, 2, kwargs=4) == "a=1, b=2, args=(), d=3, kwargs={'kwargs': 4}"
    assert foo(1, 2, kwargs=4, e=5) == "a=1, b=2, args=(), d=3, kwargs={'kwargs': 4, 'e': 5}"


def test_field_can_provide_factory() -> None:
    @validate_arguments
    def foo(a: int, b: int = Field(default_factory=lambda: 99), *args: int) -> int:
        """mypy is happy with this"""
        return a + b + sum(args)

    assert foo(3) == 102
    assert foo(1, 2, 3) == 6


def test_positional_only(create_module):
    with pytest.warns(PydanticDeprecatedSince20):
        module = create_module(
            # language=Python
            """
from pydantic.deprecated.decorator import validate_arguments

@validate_arguments
def foo(a, b, /, c=None):
    return f'{a}, {b}, {c}'
"""
        )
    assert module.foo(1, 2) == '1, 2, None'
    assert module.foo(1, 2, 44) == '1, 2, 44'
    assert module.foo(1, 2, c=44) == '1, 2, 44'
    with pytest.raises(TypeError, match="positional-only argument passed as keyword argument: 'b'"):
        module.foo(1, b=2)
    with pytest.raises(TypeError, match="positional-only arguments passed as keyword arguments: 'a', 'b'"):
        module.foo(a=1, b=2)


def test_args_name():
    @validate_arguments
    def foo(args: int, kwargs: int):
        return f'args={args!r}, kwargs={kwargs!r}'

    assert foo.model.model_fields.keys() == {'args', 'kwargs', 'v__args', 'v__kwargs', 'v__duplicate_kwargs'}
    assert foo(1, 2) == 'args=1, kwargs=2'

    with pytest.raises(TypeError, match="unexpected keyword argument: 'apple'"):
        foo(1, 2, apple=4)

    with pytest.raises(TypeError, match="unexpected keyword arguments: 'apple', 'banana'"):
        foo(1, 2, apple=4, banana=5)

    with pytest.raises(TypeError, match='2 positional arguments expected but 3 given'):
        foo(1, 2, 3)


def test_v_args():
    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_arguments
        def foo1(v__args: int):
            pass

    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_arguments
        def foo2(v__kwargs: int):
            pass

    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_arguments
        def foo3(v__positional_only: int):
            pass

    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_arguments
        def foo4(v__duplicate_kwargs: int):
            pass


def test_async():
    @validate_arguments
    async def foo(a, b):
        return f'a={a} b={b}'

    async def run():
        v = await foo(1, 2)
        assert v == 'a=1 b=2'

    asyncio.run(run())
    with pytest.raises(ValidationError) as exc_info:
        asyncio.run(foo('x'))
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'a': 'x'}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_string_annotation():
    @validate_arguments
    def foo(a: 'List[int]', b: 'Path'):
        return f'a={a!r} b={b!r}'

    assert foo([1, 2, 3], '/')

    with pytest.raises(ValidationError) as exc_info:
        foo(['x'])
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'x',
            'loc': ('a', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {'input': {'a': ['x']}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
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

    assert exc_info.value.errors(include_url=False) == [
        {'input': {'self': IsInstance(X)}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'self': IsInstance(X)}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
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

    assert exc_info.value.errors(include_url=False) == [
        {'input': {'cls': X}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'cls': X}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
    ]


def test_config_title():
    @validate_arguments(config=dict(title='Testing'))
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo.model.model_json_schema()['title'] == 'Testing'


def test_config_title_cls():
    class Config:
        title = 'Testing'

    @validate_arguments(config={'title': 'Testing'})
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo.model.model_json_schema()['title'] == 'Testing'


def test_config_fields():
    with pytest.raises(PydanticUserError, match='Setting the "alias_generator" property on custom Config for @'):

        @validate_arguments(config=dict(alias_generator=lambda x: x))
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

    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_config_arbitrary_types_allowed.<locals>.EggBox'},
            'input': 2,
            'loc': ('b',),
            'msg': 'Input should be an instance of ' 'test_config_arbitrary_types_allowed.<locals>.EggBox',
            'type': 'is_instance_of',
        }
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


def test_use_of_alias():
    @validate_arguments
    def foo(c: int = Field(default_factory=lambda: 20), a: int = Field(default_factory=lambda: 10, alias='b')):
        return a + c

    assert foo(b=10) == 30


def test_populate_by_name():
    @validate_arguments(config=dict(populate_by_name=True))
    def foo(a: Annotated[int, Field(alias='b')], c: Annotated[int, Field(alias='d')]):
        return a + c

    assert foo(a=10, d=1) == 11
    assert foo(b=10, c=1) == 11
    assert foo(a=10, c=1) == 11
