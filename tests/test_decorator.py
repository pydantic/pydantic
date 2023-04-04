import asyncio
import inspect
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pytest
from dirty_equals import IsInstance
from pydantic_core import ArgsKwargs
from typing_extensions import Annotated, TypedDict

from pydantic import Extra, Field, ValidationError, validate_call
from pydantic.errors import PydanticUserError

skip_pre_38 = pytest.mark.skipif(sys.version_info < (3, 8), reason='testing >= 3.8 behaviour only')


def test_args():
    @validate_call
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(*[1, 2]) == '1, 2'
    assert foo(*(1, 2)) == '1, 2'
    assert foo(*[1], 2) == '1, 2'
    assert foo(a=1, b=2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo(b=2, a=1) == '1, 2'

    with pytest.raises(ValidationError) as exc_info:
        foo()
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'missing_argument', 'loc': ('a',), 'msg': 'Missing required argument', 'input': ArgsKwargs(())},
        {'type': 'missing_argument', 'loc': ('b',), 'msg': 'Missing required argument', 'input': ArgsKwargs(())},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        }
    ]

    with pytest.raises(ValidationError, match=r'2\s+Unexpected positional argument'):
        foo(1, 2, 3)

    with pytest.raises(ValidationError, match=r'apple\s+Unexpected keyword argument'):
        foo(1, 2, apple=3)

    with pytest.raises(ValidationError, match=r'a\s+Got multiple values for argument'):
        foo(1, 2, a=3)

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, a=3, b=4)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'multiple_argument_values', 'loc': ('a',), 'msg': 'Got multiple values for argument', 'input': 3},
        {'type': 'multiple_argument_values', 'loc': ('b',), 'msg': 'Got multiple values for argument', 'input': 4},
    ]


def test_wrap():
    @validate_call
    def foo_bar(a: int, b: int):
        """This is the foo_bar method."""
        return f'{a}, {b}'

    assert foo_bar.__doc__ == 'This is the foo_bar method.'
    assert foo_bar.__name__ == 'foo_bar'
    assert foo_bar.__module__ == 'tests.test_decorator'
    assert foo_bar.__qualname__ == 'test_wrap.<locals>.foo_bar'
    assert isinstance(foo_bar.__pydantic_core_schema__, dict)
    assert callable(foo_bar.raw_function)
    assert repr(inspect.signature(foo_bar)) == '<Signature (a: int, b: int)>'


def test_kwargs():
    @validate_call
    def foo(*, a: int, b: int):
        return a + b

    assert foo(a=1, b=3) == 4

    with pytest.raises(ValidationError) as exc_info:
        foo(a=1, b='x')

    assert exc_info.value.errors() == [
        {
            'input': 'x',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'missing_keyword_only_argument',
            'loc': ('a',),
            'msg': 'Missing required keyword only argument',
            'input': ArgsKwargs((1, 'x')),
        },
        {
            'type': 'missing_keyword_only_argument',
            'loc': ('b',),
            'msg': 'Missing required keyword only argument',
            'input': ArgsKwargs((1, 'x')),
        },
        {'type': 'unexpected_positional_argument', 'loc': (0,), 'msg': 'Unexpected positional argument', 'input': 1},
        {'type': 'unexpected_positional_argument', 'loc': (1,), 'msg': 'Unexpected positional argument', 'input': 'x'},
    ]


def test_untyped():
    @validate_call
    def foo(a, b, c='x', *, d='y'):
        return ', '.join(str(arg) for arg in [a, b, c, d])

    assert foo(1, 2) == '1, 2, x, y'
    assert foo(1, {'x': 2}, c='3', d='4') == "1, {'x': 2}, 3, 4"


@pytest.mark.parametrize('validated', (True, False))
def test_var_args_kwargs(validated):
    def foo(a, b, *args, d=3, **kwargs):
        return f'a={a!r}, b={b!r}, args={args!r}, d={d!r}, kwargs={kwargs!r}'

    if validated:
        foo = validate_call(foo)

    assert foo(1, 2) == 'a=1, b=2, args=(), d=3, kwargs={}'
    assert foo(1, 2, 3, d=4) == 'a=1, b=2, args=(3,), d=4, kwargs={}'
    assert foo(*[1, 2, 3], d=4) == 'a=1, b=2, args=(3,), d=4, kwargs={}'
    assert foo(1, 2, args=(10, 11)) == "a=1, b=2, args=(), d=3, kwargs={'args': (10, 11)}"
    assert foo(1, 2, 3, args=(10, 11)) == "a=1, b=2, args=(3,), d=3, kwargs={'args': (10, 11)}"
    assert foo(1, 2, 3, e=10) == "a=1, b=2, args=(3,), d=3, kwargs={'e': 10}"
    assert foo(1, 2, kwargs=4) == "a=1, b=2, args=(), d=3, kwargs={'kwargs': 4}"
    assert foo(1, 2, kwargs=4, e=5) == "a=1, b=2, args=(), d=3, kwargs={'kwargs': 4, 'e': 5}"


@pytest.mark.xfail(reason='what do we do about Field?')
def test_field_can_provide_factory() -> None:
    @validate_call
    def foo(a: int, b: int = Field(default_factory=lambda: 99), *args: int) -> int:
        """mypy is happy with this"""
        return a + b + sum(args)

    assert foo(3) == 102
    assert foo(1, 2, 3) == 6


@pytest.mark.xfail(reason='what do we do about Field?')
def test_annotated_field_can_provide_factory() -> None:
    @validate_call
    def foo2(a: int, b: Annotated[int, Field(default_factory=lambda: 99)], *args: int) -> int:
        """mypy reports Incompatible default for argument "b" if we don't supply ANY as default"""
        return a + b + sum(args)

    assert foo2(1) == 100


@skip_pre_38
def test_positional_only(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import validate_call

@validate_call
def foo(a, b, /, c=None):
    return f'{a}, {b}, {c}'
"""
    )
    assert module.foo(1, 2) == '1, 2, None'
    assert module.foo(1, 2, 44) == '1, 2, 44'
    assert module.foo(1, 2, c=44) == '1, 2, 44'
    with pytest.raises(ValidationError) as exc_info:
        module.foo(1, b=2)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'missing_positional_only_argument',
            'loc': (1,),
            'msg': 'Missing required positional only argument',
            'input': ArgsKwargs((1,), {'b': 2}),
        },
        {'type': 'unexpected_keyword_argument', 'loc': ('b',), 'msg': 'Unexpected keyword argument', 'input': 2},
    ]

    with pytest.raises(ValidationError) as exc_info:
        module.foo(a=1, b=2)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'missing_positional_only_argument',
            'loc': (0,),
            'msg': 'Missing required positional only argument',
            'input': ArgsKwargs((), {'a': 1, 'b': 2}),
        },
        {
            'type': 'missing_positional_only_argument',
            'loc': (1,),
            'msg': 'Missing required positional only argument',
            'input': ArgsKwargs((), {'a': 1, 'b': 2}),
        },
        {'type': 'unexpected_keyword_argument', 'loc': ('a',), 'msg': 'Unexpected keyword argument', 'input': 1},
        {'type': 'unexpected_keyword_argument', 'loc': ('b',), 'msg': 'Unexpected keyword argument', 'input': 2},
    ]


def test_args_name():
    @validate_call
    def foo(args: int, kwargs: int):
        return f'args={args!r}, kwargs={kwargs!r}'

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

        @validate_call
        def foo1(v__args: int):
            pass

    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_call
        def foo2(v__kwargs: int):
            pass

    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_call
        def foo3(v__positional_only: int):
            pass

    with pytest.raises(
        PydanticUserError,
        match='"v__args", "v__kwargs", "v__positional_only" and "v__duplicate_kwargs" are not permitted',
    ):

        @validate_call
        def foo4(v__duplicate_kwargs: int):
            pass


def test_async():
    @validate_call
    async def foo(a, b):
        return f'a={a} b={b}'

    async def run():
        v = await foo(1, 2)
        assert v == 'a=1 b=2'

    asyncio.run(run())
    with pytest.raises(ValidationError) as exc_info:
        asyncio.run(foo('x'))
    assert exc_info.value.errors() == [{'input': {'a': 'x'}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'}]


def test_string_annotation():
    @validate_call
    def foo(a: 'List[int]', b: 'Path'):
        return f'a={a!r} b={b!r}'

    assert foo([1, 2, 3], '/')

    with pytest.raises(ValidationError) as exc_info:
        foo(['x'])
    assert exc_info.value.errors() == [
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

        @validate_call
        def foo(self, a: int, b: int):
            assert self.v == a
            return f'{a}, {b}'

    x = X(4)
    assert x.foo(4, 2) == '4, 2'
    assert x.foo(*[4, 2]) == '4, 2'

    with pytest.raises(ValidationError) as exc_info:
        x.foo()

    assert exc_info.value.errors() == [
        {'input': {'self': IsInstance(X)}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'self': IsInstance(X)}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
    ]


def test_class_method():
    class X:
        @classmethod
        @validate_call
        def foo(cls, a: int, b: int):
            assert cls == X
            return f'{a}, {b}'

    x = X()
    assert x.foo(4, 2) == '4, 2'
    assert x.foo(*[4, 2]) == '4, 2'

    with pytest.raises(ValidationError) as exc_info:
        x.foo()

    assert exc_info.value.errors() == [
        {'input': {'cls': X}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'cls': X}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
    ]


def test_config_title():
    @validate_call(config=dict(title='Testing'))
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo.model.model_json_schema()['title'] == 'Testing'


def test_config_title_cls():
    class Config:
        title = 'Testing'

    @validate_call(config={'title': 'Testing'})
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo.model.model_json_schema()['title'] == 'Testing'


def test_config_fields():
    with pytest.raises(PydanticUserError, match='Setting the "alias_generator" property on custom Config for @'):

        @validate_call(config=dict(alias_generator=lambda x: x))
        def foo(a: int, b: int):
            return f'{a}, {b}'


def test_config_arbitrary_types_allowed():
    class EggBox:
        def __str__(self) -> str:
            return 'EggBox()'

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def foo(a: int, b: EggBox):
        return f'{a}, {b}'

    assert foo(1, EggBox()) == '1, EggBox()'
    with pytest.raises(ValidationError) as exc_info:
        assert foo(1, 2) == '1, 2'

    assert exc_info.value.errors() == [
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

    @validate_call
    def func(s: str, count: int, *, separator: bytes = b''):
        stub(s, count, separator)

    func.validate('qwe', 2)
    with pytest.raises(ValidationError):
        func.validate(['qwe'], 2)

    stub.assert_not_called()


@pytest.mark.xfail(reason='Annotated does not seem to be respected')
def test_annotated_use_of_alias():
    @validate_call
    def foo(a: Annotated[int, Field(alias='b')], c: Annotated[int, Field()], d: Annotated[int, Field(alias='')]):
        return a + c + d

    assert foo(**{'b': 10, 'c': 12, '': 1}) == 23

    with pytest.raises(ValidationError) as exc_info:
        assert foo(a=10, c=12, d=1) == 10

    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('a',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
        {'loc': ('d',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_use_of_alias():
    @validate_call
    def foo(c: int = Field(default_factory=lambda: 20), a: int = Field(default_factory=lambda: 10, alias='b')):
        return a + c

    assert foo(b=10) == 30


def test_populate_by_name():
    @validate_call(config=dict(populate_by_name=True))
    def foo(a: Annotated[int, Field(alias='b')], c: Annotated[int, Field(alias='d')]):
        return a + c

    assert foo(a=10, d=1) == 11
    assert foo(b=10, c=1) == 11
    assert foo(a=10, c=1) == 11


@pytest.mark.xfail(reason='validate_all')
def test_validate_all():
    # TODO remove or rename, validate_all doesn't exist anymore
    @validate_call(config=dict(validate_all=True))
    def foo(dt: datetime = Field(default_factory=lambda: 946684800)):
        return dt

    assert foo() == datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert foo(0) == datetime(1970, 1, 1, tzinfo=timezone.utc)


@pytest.mark.xfail(reason='validate_all')
@skip_pre_38
def test_validate_all_positional(create_module):
    # TODO remove or rename, validate_all doesn't exist anymore
    module = create_module(
        # language=Python
        """
from datetime import datetime

from pydantic import Field, validate_call

@validate_call(config=dict(validate_all=True))
def foo(dt: datetime = Field(default_factory=lambda: 946684800), /):
    return dt
"""
    )
    assert module.foo() == datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert module.foo(0) == datetime(1970, 1, 1, tzinfo=timezone.utc)


@pytest.mark.xfail(reason='config["extra"] does not seem to be respected')
def test_validate_extra():
    class TypedTest(TypedDict):
        y: str

    @validate_call(config={'extra': Extra.allow})
    def test(other: TypedTest):
        return other

    assert test(other={'y': 'b', 'z': 'a'}) == {'y': 'b', 'z': 'a'}

    @validate_call(config={'extra': Extra.ignore})
    def test(other: TypedTest):
        return other

    assert test(other={'y': 'b', 'z': 'a'}) == {'y': 'b'}
