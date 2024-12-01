??? api "API Documentation"
    [`pydantic.validate_call_decorator.validate_call`][pydantic.validate_call_decorator.validate_call]<br>

The [`validate_call()`][pydantic.validate_call] decorator allows the arguments passed to a function to be parsed
and validated using the function's annotations before the function is called.

While under the hood this uses the same approach of model creation and initialisation
(see [Validators](validators.md) for more details), it provides an extremely easy way to apply validation
to your code with minimal boilerplate.

Example of usage:

```python
from pydantic import ValidationError, validate_call


@validate_call
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat('x', '4', separator=b' ')
print(b)
#> b'x x x x'

try:
    c = repeat('hello', 'wrong')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for repeat
    1
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """
```

## Parameter types

Parameter types are inferred from type annotations on the function, or as [`Any`][typing.Any] if not annotated. All types listed in [types](types.md) can be validated, including Pydantic models and [custom types](types.md#custom-types).
As with the rest of Pydantic, types are by default coerced by the decorator before they're passed to the actual function:

```python
from datetime import date

from pydantic import validate_call


@validate_call
def greater_than(d1: date, d2: date, *, include_equal=False) -> date:  # (1)!
    if include_equal:
        return d1 >= d2
    else:
        return d1 > d2


d1 = '2000-01-01'  # (2)!
d2 = date(2001, 1, 1)
greater_than(d1, d2, include_equal=True)
```

1. Because `include_equal` has no type annotation, it will be inferred as [`Any`][typing.Any].
2. Although `d1` is a string, it will be converted to a [`date`][datetime.date] object.

Type coercion like this can be extremely helpful, but also confusing or not desired (see [model data conversion](models.md#data-conversion)). [Strict mode](strict_mode.md)
can be enabled by using a [custom configuration](#custom-configuration).

!!! note "Validating the return value"
    By default, the return value of the function is **not** validated. To do so, the `validate_return` argument
    of the decorator can be set to `True`.

## Function signatures

The [`validate_call()`][pydantic.validate_call] decorator is designed to work with functions
using all possible [parameter configurations][parameter] and all possible combinations of these:

* Positional or keyword parameters with or without defaults.
* Keyword-only parameters: parameters after `*,`.
* Positional-only parameters: parameters before `, /`.
* Variable positional parameters defined via `*` (often `*args`).
* Variable keyword parameters defined via `**` (often `**kwargs`).

??? example

    ```python
    from pydantic import validate_call


    @validate_call
    def pos_or_kw(a: int, b: int = 2) -> str:
        return f'a={a} b={b}'


    print(pos_or_kw(1, b=3))
    #> a=1 b=3


    @validate_call
    def kw_only(*, a: int, b: int = 2) -> str:
        return f'a={a} b={b}'


    print(kw_only(a=1))
    #> a=1 b=2
    print(kw_only(a=1, b=3))
    #> a=1 b=3


    @validate_call
    def pos_only(a: int, b: int = 2, /) -> str:
        return f'a={a} b={b}'


    print(pos_only(1))
    #> a=1 b=2


    @validate_call
    def var_args(*args: int) -> str:
        return str(args)


    print(var_args(1))
    #> (1,)
    print(var_args(1, 2, 3))
    #> (1, 2, 3)


    @validate_call
    def var_kwargs(**kwargs: int) -> str:
        return str(kwargs)


    print(var_kwargs(a=1))
    #> {'a': 1}
    print(var_kwargs(a=1, b=2))
    #> {'a': 1, 'b': 2}


    @validate_call
    def armageddon(
        a: int,
        /,
        b: int,
        *c: int,
        d: int,
        e: int = None,
        **f: int,
    ) -> str:
        return f'a={a} b={b} c={c} d={d} e={e} f={f}'


    print(armageddon(1, 2, d=3))
    #> a=1 b=2 c=() d=3 e=None f={}
    print(armageddon(1, 2, 3, 4, 5, 6, d=8, e=9, f=10, spam=11))
    #> a=1 b=2 c=(3, 4, 5, 6) d=8 e=9 f={'f': 10, 'spam': 11}
    ```

!!! note "[`Unpack`][typing.Unpack] for keyword parameters"
    [`Unpack`][typing.Unpack] and typed dictionaries can be used to annotate the variable
    keyword parameters of a function:

    ```python
    from typing_extensions import TypedDict, Unpack

    from pydantic import validate_call


    class Point(TypedDict):
        x: int
        y: int


    @validate_call
    def add_coords(**kwargs: Unpack[Point]) -> int:
        return kwargs['x'] + kwargs['y']


    add_coords(x=1, y=2)
    ```

    For reference, see the [related specification section] and [PEP 692].

    [related specification section]: https://typing.readthedocs.io/en/latest/spec/callables.html#unpack-for-keyword-arguments
    [PEP 692]: https://peps.python.org/pep-0692/

## Using the [`Field()`][pydantic.Field] function to describe function parameters

The [`Field()` function](fields.md) can also be used with the decorator to provide extra information about
the field and validations. In general it should be used in a type hint with [Annotated](types.md#composing-types-via-annotated),
unless `default_factory` is specified, in which case it should be used as the default value of the field:

```python
from datetime import datetime

from typing_extensions import Annotated

from pydantic import Field, ValidationError, validate_call


@validate_call
def how_many(num: Annotated[int, Field(gt=10)]):
    return num


try:
    how_many(1)
except ValidationError as e:
    print(e)
    """
    1 validation error for how_many
    0
      Input should be greater than 10 [type=greater_than, input_value=1, input_type=int]
    """


@validate_call
def when(dt: datetime = Field(default_factory=datetime.now)):
    return dt


print(type(when()))
#> <class 'datetime.datetime'>
```

[Aliases](fields.md#field-aliases) can be used with the decorator as normal:

```python
from typing_extensions import Annotated

from pydantic import Field, validate_call


@validate_call
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num


how_many(number=42)
```

## Accessing the original function

The original function which was decorated can still be accessed by using the `raw_function` attribute.
This is useful if in some scenarios you trust your input arguments and want to call the function in the most efficient way (see [notes on performance](#performance) below):

```python
from pydantic import validate_call


@validate_call
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat.raw_function('good bye', 2, separator=b', ')
print(b)
#> b'good bye, good bye'
```

## Async functions

[`validate_call()`][pydantic.validate_call] can also be used on async functions:

```python
class Connection:
    async def execute(self, sql, *args):
        return 'testing@example.com'


conn = Connection()
# ignore-above
import asyncio

from pydantic import PositiveInt, ValidationError, validate_call


@validate_call
async def get_user_email(user_id: PositiveInt):
    # `conn` is some fictional connection to a database
    email = await conn.execute('select email from users where id=$1', user_id)
    if email is None:
        raise RuntimeError('user not found')
    else:
        return email


async def main():
    email = await get_user_email(123)
    print(email)
    #> testing@example.com
    try:
        await get_user_email(-4)
    except ValidationError as exc:
        print(exc.errors())
        """
        [
            {
                'type': 'greater_than',
                'loc': (0,),
                'msg': 'Input should be greater than 0',
                'input': -4,
                'ctx': {'gt': 0},
                'url': 'https://errors.pydantic.dev/2/v/greater_than',
            }
        ]
        """


asyncio.run(main())
# requires: `conn.execute()` that will return `'testing@example.com'`
```

## Compatibility with type checkers

As the [`validate_call()`][pydantic.validate_call] decorator preserves the decorated function's signature,
it should be compatible with type checkers (such as mypy and pyright). However, due to current limitations in the Python type system,
the [`raw_function`](#accessing-the-original-function) or other attributes won't be recognized and you will
need to suppress the error using (usually with a `# type: ignore` comment).

## Custom configuration

Similarly to Pydantic models, the `config` parameter of the decorator can be used to specify a custom configuration:

```python
from pydantic import ConfigDict, ValidationError, validate_call


class Foobar:
    def __init__(self, v: str):
        self.v = v

    def __add__(self, other: 'Foobar') -> str:
        return f'{self} + {other}'

    def __str__(self) -> str:
        return f'Foobar({self.v})'


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def add_foobars(a: Foobar, b: Foobar):
    return a + b


c = add_foobars(Foobar('a'), Foobar('b'))
print(c)
#> Foobar(a) + Foobar(b)

try:
    add_foobars(1, 2)
except ValidationError as e:
    print(e)
    """
    2 validation errors for add_foobars
    0
      Input should be an instance of Foobar [type=is_instance_of, input_value=1, input_type=int]
    1
      Input should be an instance of Foobar [type=is_instance_of, input_value=2, input_type=int]
    """
```

## Extension — validating arguments before calling a function

In some cases, it may be helpful to separate validation of a function's arguments from the function call itself.
This might be useful when a particular function is costly/time consuming.

Here's an example of a workaround you can use for that pattern:

```python
from pydantic import validate_call


@validate_call
def validate_foo(a: int, b: int):
    def foo():
        return a + b

    return foo


foo = validate_foo(a=1, b=2)
print(foo())
#> 3
```

## Limitations

### Validation exception

Currently upon validation failure, a standard Pydantic [`ValidationError`][pydantic_core.ValidationError] is raised
(see [model error handling](models.md#error-handling) for details). This is also true for missing required arguments,
where Python normally raises a [`TypeError`][].

### Performance

We've made a big effort to make Pydantic as performant as possible. While the inspection of the decorated
function is only performed once, there will still be a performance impact when making calls to the function
compared to using the original function.

In many situations, this will have little or no noticeable effect. However, be aware that
[`validate_call()`][pydantic.validate_call] is not an equivalent or alternative to function
definitions in strongly typed languages, and it never will be.
