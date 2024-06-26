import asyncio
import inspect
import re
import sys
from datetime import datetime, timezone
from functools import partial
from typing import Any, List, Tuple

import pytest
from pydantic_core import ArgsKwargs
from typing_extensions import Annotated, TypedDict

from pydantic import Field, PydanticInvalidForJsonSchema, TypeAdapter, ValidationError, validate_call
from pydantic.main import BaseModel


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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing_argument', 'loc': ('a',), 'msg': 'Missing required argument', 'input': ArgsKwargs(())},
        {'type': 'missing_argument', 'loc': ('b',), 'msg': 'Missing required argument', 'input': ArgsKwargs(())},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'multiple_argument_values', 'loc': ('a',), 'msg': 'Got multiple values for argument', 'input': 3},
        {'type': 'multiple_argument_values', 'loc': ('b',), 'msg': 'Got multiple values for argument', 'input': 4},
    ]


def test_optional():
    @validate_call
    def foo_bar(a: int = None):
        return f'a={a}'

    assert foo_bar() == 'a=None'
    assert foo_bar(1) == 'a=1'
    with pytest.raises(ValidationError) as exc_info:
        foo_bar(None)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (0,), 'msg': 'Input should be a valid integer', 'input': None}
    ]


def test_wrap():
    @validate_call
    def foo_bar(a: int, b: int):
        """This is the foo_bar method."""
        return f'{a}, {b}'

    assert foo_bar.__doc__ == 'This is the foo_bar method.'
    assert foo_bar.__name__ == 'foo_bar'
    assert foo_bar.__module__ == 'tests.test_validate_call'
    assert foo_bar.__qualname__ == 'test_wrap.<locals>.foo_bar'
    assert callable(foo_bar.raw_function)
    assert repr(inspect.signature(foo_bar)) == '<Signature (a: int, b: int)>'


def test_kwargs():
    @validate_call
    def foo(*, a: int, b: int):
        return a + b

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

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 'x')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
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


def test_field_can_provide_factory() -> None:
    @validate_call
    def foo(a: int, b: int = Field(default_factory=lambda: 99), *args: int) -> int:
        """mypy is happy with this"""
        return a + b + sum(args)

    assert foo(3) == 102
    assert foo(1, 2, 3) == 6


def test_annotated_field_can_provide_factory() -> None:
    @validate_call
    def foo2(a: int, b: Annotated[int, Field(default_factory=lambda: 99)], *args: int) -> int:
        """mypy reports Incompatible default for argument "b" if we don't supply ANY as default"""
        return a + b + sum(args)

    assert foo2(1) == 100


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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
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

    with pytest.raises(ValidationError, match=r'apple\s+Unexpected keyword argument'):
        foo(1, 2, apple=4)

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, apple=4, banana=5)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'unexpected_keyword_argument', 'loc': ('apple',), 'msg': 'Unexpected keyword argument', 'input': 4},
        {'type': 'unexpected_keyword_argument', 'loc': ('banana',), 'msg': 'Unexpected keyword argument', 'input': 5},
    ]

    with pytest.raises(ValidationError) as exc_info:
        foo(1, 2, 3)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'unexpected_positional_argument', 'loc': (2,), 'msg': 'Unexpected positional argument', 'input': 3}
    ]


def test_v_args():
    @validate_call
    def foo1(v__args: int):
        return v__args

    assert foo1(123) == 123

    @validate_call
    def foo2(v__kwargs: int):
        return v__kwargs

    assert foo2(123) == 123

    @validate_call
    def foo3(v__positional_only: int):
        return v__positional_only

    assert foo3(123) == 123

    @validate_call
    def foo4(v__duplicate_kwargs: int):
        return v__duplicate_kwargs

    assert foo4(123) == 123


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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing_argument', 'loc': ('b',), 'msg': 'Missing required argument', 'input': ArgsKwargs(('x',))}
    ]


def test_string_annotation():
    @validate_call
    def foo(a: 'List[int]', b: 'float'):
        return f'a={a!r} b={b!r}'

    assert foo([1, 2, 3], 22) == 'a=[1, 2, 3] b=22.0'

    with pytest.raises(ValidationError) as exc_info:
        foo(['x'])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0, 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {'type': 'missing_argument', 'loc': ('b',), 'msg': 'Missing required argument', 'input': ArgsKwargs((['x'],))},
    ]


def test_local_annotation():
    ListInt = List[int]

    @validate_call
    def foo(a: ListInt):
        return f'a={a!r}'

    assert foo([1, 2, 3]) == 'a=[1, 2, 3]'

    with pytest.raises(ValidationError) as exc_info:
        foo(['x'])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0, 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
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

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing_argument', 'loc': ('a',), 'msg': 'Missing required argument', 'input': ArgsKwargs((x,))},
        {'type': 'missing_argument', 'loc': ('b',), 'msg': 'Missing required argument', 'input': ArgsKwargs((x,))},
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

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing_argument', 'loc': ('a',), 'msg': 'Missing required argument', 'input': ArgsKwargs((X,))},
        {'type': 'missing_argument', 'loc': ('b',), 'msg': 'Missing required argument', 'input': ArgsKwargs((X,))},
    ]


def test_json_schema():
    @validate_call
    def foo(a: int, b: int = None):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(1, b=2) == '1, 2'
    assert foo(1) == '1, None'
    assert TypeAdapter(foo).json_schema() == {
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'integer'}, 'b': {'default': None, 'title': 'B', 'type': 'integer'}},
        'required': ['a'],
        'additionalProperties': False,
    }

    @validate_call
    def foo(a: int, /, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert TypeAdapter(foo).json_schema() == {
        'maxItems': 2,
        'minItems': 2,
        'prefixItems': [{'title': 'A', 'type': 'integer'}, {'title': 'B', 'type': 'integer'}],
        'type': 'array',
    }

    @validate_call
    def foo(a: int, /, *, b: int, c: int):
        return f'{a}, {b}, {c}'

    assert foo(1, b=2, c=3) == '1, 2, 3'
    with pytest.raises(
        PydanticInvalidForJsonSchema,
        match=(
            'Unable to generate JSON schema for arguments validator ' 'with positional-only and keyword-only arguments'
        ),
    ):
        TypeAdapter(foo).json_schema()

    @validate_call
    def foo(*numbers: int) -> int:
        return sum(numbers)

    assert foo(1, 2, 3) == 6
    assert TypeAdapter(foo).json_schema() == {'items': {'type': 'integer'}, 'prefixItems': [], 'type': 'array'}

    @validate_call
    def foo(**scores: int) -> str:
        return ', '.join(f'{k}={v}' for k, v in sorted(scores.items()))

    assert foo(a=1, b=2) == 'a=1, b=2'
    assert TypeAdapter(foo).json_schema() == {
        'additionalProperties': {'type': 'integer'},
        'properties': {},
        'type': 'object',
    }

    @validate_call
    def foo(a: Annotated[int, Field(..., alias='A')]):
        return a

    assert foo(1) == 1
    assert TypeAdapter(foo).json_schema() == {
        'additionalProperties': False,
        'properties': {'A': {'title': 'A', 'type': 'integer'}},
        'required': ['A'],
        'type': 'object',
    }


def test_alias_generator():
    @validate_call(config=dict(alias_generator=lambda x: x * 2))
    def foo(a: int, b: int):
        return f'{a}, {b}'

    assert foo(1, 2) == '1, 2'
    assert foo(aa=1, bb=2) == '1, 2'


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

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (1,),
            'msg': 'Input should be an instance of test_config_arbitrary_types_allowed.<locals>.EggBox',
            'input': 2,
            'ctx': {'class': 'test_config_arbitrary_types_allowed.<locals>.EggBox'},
        }
    ]


def test_config_strict():
    @validate_call(config=dict(strict=True))
    def foo(a: int, b: List[str]):
        return f'{a}, {b[0]}'

    assert foo(1, ['bar', 'foobar']) == '1, bar'
    with pytest.raises(ValidationError) as exc_info:
        foo('foo', ('bar', 'foobar'))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (0,), 'msg': 'Input should be a valid integer', 'input': 'foo'},
        {'type': 'list_type', 'loc': (1,), 'msg': 'Input should be a valid list', 'input': ('bar', 'foobar')},
    ]


def test_annotated_use_of_alias():
    @validate_call
    def foo(a: Annotated[int, Field(alias='b')], c: Annotated[int, Field()], d: Annotated[int, Field(alias='')]):
        return a + c + d

    assert foo(**{'b': 10, 'c': 12, '': 1}) == 23

    with pytest.raises(ValidationError) as exc_info:
        assert foo(a=10, c=12, d=1) == 10

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing_argument',
            'loc': ('b',),
            'msg': 'Missing required argument',
            'input': ArgsKwargs((), {'a': 10, 'c': 12, 'd': 1}),
        },
        {
            'type': 'missing_argument',
            'loc': ('',),
            'msg': 'Missing required argument',
            'input': ArgsKwargs((), {'a': 10, 'c': 12, 'd': 1}),
        },
        {'type': 'unexpected_keyword_argument', 'loc': ('a',), 'msg': 'Unexpected keyword argument', 'input': 10},
        {'type': 'unexpected_keyword_argument', 'loc': ('d',), 'msg': 'Unexpected keyword argument', 'input': 1},
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

    assert foo(b=10, d=1) == 11
    assert foo(a=10, d=1) == 11
    assert foo(b=10, c=1) == 11
    assert foo(a=10, c=1) == 11


def test_validate_return():
    @validate_call(config=dict(validate_return=True))
    def foo(a: int, b: int) -> int:
        return a + b

    assert foo(1, 2) == 3


def test_validate_all():
    @validate_call(config=dict(validate_default=True))
    def foo(dt: datetime = Field(default_factory=lambda: 946684800)):
        return dt

    assert foo() == datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert foo(0) == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_validate_all_positional(create_module):
    module = create_module(
        # language=Python
        """
from datetime import datetime

from pydantic import Field, validate_call

@validate_call(config=dict(validate_default=True))
def foo(dt: datetime = Field(default_factory=lambda: 946684800), /):
    return dt
"""
    )
    assert module.foo() == datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert module.foo(0) == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_partial():
    def my_wrapped_function(a: int, b: int, c: int):
        return a + b + c

    my_partial_function = partial(my_wrapped_function, c=3)
    f = validate_call(my_partial_function)
    assert f(1, 2) == 6


def test_validator_init():
    class Foo:
        @validate_call
        def __init__(self, a: int, b: int):
            self.v = a + b

    assert Foo(1, 2).v == 3
    assert Foo(1, '2').v == 3
    with pytest.raises(ValidationError, match="type=int_parsing, input_value='x', input_type=str"):
        Foo(1, 'x')


def test_positional_and_keyword_with_same_name(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import validate_call

@validate_call
def f(a: int, /, **kwargs):
    return a, kwargs
"""
    )
    assert module.f(1, a=2) == (1, {'a': 2})


def test_model_as_arg() -> None:
    class Model1(TypedDict):
        x: int

    class Model2(BaseModel):
        y: int

    @validate_call(validate_return=True)
    def f1(m1: Model1, m2: Model2) -> Tuple[Model1, Model2]:
        return (m1, m2.model_dump())  # type: ignore

    res = f1({'x': '1'}, {'y': '2'})  # type: ignore
    assert res == ({'x': 1}, Model2(y=2))


def test_do_not_call_repr_on_validate_call() -> None:
    class Class:
        @validate_call
        def __init__(self, number: int) -> None: ...

        def __repr__(self) -> str:
            assert False

    Class(50)


def test_methods_are_not_rebound():
    class Thing:
        def __init__(self, x: int):
            self.x = x

        def a(self, x: int):
            return x + self.x

        c = validate_call(a)

    thing = Thing(1)
    assert thing.a == thing.a
    assert thing.c == thing.c
    assert Thing.c == Thing.c

    # Ensure validation is still happening
    assert Thing.c(thing, '2') == 3
    assert Thing(2).c('3') == 5


def test_basemodel_method():
    class Foo(BaseModel):
        @classmethod
        @validate_call
        def test(cls, x: int):
            return cls, x

    assert Foo.test('1') == (Foo, 1)

    class Bar(BaseModel):
        @validate_call
        def test(self, x: int):
            return self, x

    bar = Bar()
    assert bar.test('1') == (bar, 1)


def test_dynamic_method_decoration():
    class Foo:
        def bar(self, value: str) -> str:
            return f'bar-{value}'

    Foo.bar = validate_call(Foo.bar)
    assert Foo.bar

    foo = Foo()
    assert foo.bar('test') == 'bar-test'


@pytest.mark.parametrize('decorator', [staticmethod, classmethod])
def test_classmethod_order_error(decorator):
    name = decorator.__name__
    with pytest.raises(
        TypeError,
        match=re.escape(f'The `@{name}` decorator should be applied after `@validate_call` (put `@{name}` on top)'),
    ):

        class A:
            @validate_call
            @decorator
            def method(self, x: int):
                pass


def test_async_func() -> None:
    @validate_call(validate_return=True)
    async def foo(a: Any) -> int:
        return a

    res = asyncio.run(foo(1))
    assert res == 1

    with pytest.raises(ValidationError) as exc_info:
        asyncio.run(foo('x'))

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        }
    ]


def test_validate_call_with_slots() -> None:
    class ClassWithSlots:
        __slots__ = {}

        @validate_call(validate_return=True)
        def some_instance_method(self, x: str) -> str:
            return x

        @classmethod
        @validate_call(validate_return=True)
        def some_class_method(cls, x: str) -> str:
            return x

        @staticmethod
        @validate_call(validate_return=True)
        def some_static_method(x: str) -> str:
            return x

    c = ClassWithSlots()
    assert c.some_instance_method(x='potato') == 'potato'
    assert c.some_class_method(x='pepper') == 'pepper'
    assert c.some_static_method(x='onion') == 'onion'

    # verify that equality still holds for instance methods
    assert c.some_instance_method == c.some_instance_method
    assert c.some_class_method == c.some_class_method
    assert c.some_static_method == c.some_static_method


def test_eval_type_backport():
    @validate_call
    def foo(bar: 'list[int | str]') -> 'list[int | str]':
        return bar

    assert foo([1, '2']) == [1, '2']
    with pytest.raises(ValidationError) as exc_info:
        foo('not a list')  # type: ignore
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': (0,),
            'msg': 'Input should be a valid list',
            'input': 'not a list',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        foo([{'not a str or int'}])  # type: ignore
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_type',
            'loc': (0, 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': {'not a str or int'},
        },
        {
            'type': 'string_type',
            'loc': (0, 0, 'str'),
            'msg': 'Input should be a valid string',
            'input': {'not a str or int'},
        },
    ]


@pytest.mark.skipif(sys.version_info < (3, 12), reason='requires Python 3.12+ for PEP 695 syntax with generics')
def test_validate_call_with_pep_695_syntax() -> None:
    """Note: validate_call still doesn't work properly with generics, see https://github.com/pydantic/pydantic/issues/7796.

    This test is just to ensure that the syntax is accepted and doesn't raise a NameError."""
    globs = {}
    exec(
        """
from typing import Iterable
from pydantic import validate_call

@validate_call
def find_max_no_validate_return[T](args: Iterable[T]) -> T:
    return sorted(args, reverse=True)[0]

@validate_call(validate_return=True)
def find_max_validate_return[T](args: Iterable[T]) -> T:
    return sorted(args, reverse=True)[0]
        """,
        globs,
    )
    functions = [globs['find_max_no_validate_return'], globs['find_max_validate_return']]
    for find_max in functions:
        assert len(find_max.__type_params__) == 1
        assert find_max([1, 2, 10, 5]) == 10

        with pytest.raises(ValidationError):
            find_max(1)


class M0(BaseModel):
    z: int


M = M0


def test_uses_local_ns():
    class M1(BaseModel):
        y: int

    M = M1  # noqa: F841

    def foo():
        class M2(BaseModel):
            z: int

        M = M2

        @validate_call
        def bar(m: M) -> M:
            return m

        assert bar({'z': 1}) == M2(z=1)
