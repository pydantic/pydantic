The `validate_arguments` decorator allows the arguments passed to a function to be parsed and validated using
the function's annotations before the function is called. While under the hood this uses the same approach of model
creation and initialisation; it provides an extremely easy way to apply validation to your code with minimal
boilerplate.

!!! info "In Beta"
    The `validate_arguments` decorator is in **beta**, it has been added to *pydantic* in **v1.5** on a
    **provisional basis**. It may change significantly in future releases and its interface will not be concrete
    until **v2**. Feedback from the community while it's still provisional would be extremely useful; either comment
    on [#1205](https://github.com/pydantic/pydantic/issues/1205) or create a new issue.

Example of usage:

```py
from pydantic import ValidationError, validate_arguments


@validate_arguments
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat('x', '4', separator=' ')
print(b)
#> b'x x x x'

try:
    c = repeat('hello', 'wrong')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Repeat
    count
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """
```

## Argument Types

Argument types are inferred from type annotations on the function, arguments without a type decorator are considered
as `Any`. All types listed in [types](types.md) can be validated, including *pydantic* models and
[custom types](types.md#custom-data-types).
As with the rest of *pydantic*, types can be coerced by the decorator before they're passed to the actual function:

```py test="no-print-intercept"
# TODO replace find_file with something that isn't affected the filesystem
import os
from pathlib import Path
from typing import Optional, Pattern

from pydantic import DirectoryPath, validate_arguments


@validate_arguments
def find_file(path: DirectoryPath, regex: Pattern, max=None) -> Optional[Path]:
    for i, f in enumerate(path.glob('**/*')):
        if max and i > max:
            return
        if f.is_file() and regex.fullmatch(str(f.relative_to(path))):
            return f


# note: this_dir is a string here
this_dir = os.path.dirname(__file__)

print(find_file(this_dir, '^validation.*'))
print(find_file(this_dir, '^foobar.*', max=3))
```

A few notes:

- though they're passed as strings, `path` and `regex` are converted to a `Path` object and regex respectively
by the decorator
- `max` has no type annotation, so will be considered as `Any` by the decorator

Type coercion like this can be extremely helpful but also confusing or not desired,
see [below](#coercion-and-strictness) for a discussion of `validate_arguments`'s limitations in this regard.

## Function Signatures

The decorator is designed to work with functions using all possible parameter configurations and all possible
combinations of these:

* positional or keyword arguments with or without defaults
* variable positional arguments defined via `*` (often `*args`)
* variable keyword arguments defined via `**` (often `**kwargs`)
* keyword only arguments - arguments after `*,`
* positional only arguments - arguments before `, /` (new in Python 3.8)

To demonstrate all the above parameter types:

```py require="3.8"
from pydantic import validate_arguments


@validate_arguments
def pos_or_kw(a: int, b: int = 2) -> str:
    return f'a={a} b={b}'


print(pos_or_kw(1))
#> a=1 b=2
print(pos_or_kw(a=1))
#> a=1 b=2
print(pos_or_kw(1, 3))
#> a=1 b=3
print(pos_or_kw(a=1, b=3))
#> a=1 b=3


@validate_arguments
def kw_only(*, a: int, b: int = 2) -> str:
    return f'a={a} b={b}'


print(kw_only(a=1))
#> a=1 b=2
print(kw_only(a=1, b=3))
#> a=1 b=3


@validate_arguments
def pos_only(a: int, b: int = 2, /) -> str:  # python 3.8 only
    return f'a={a} b={b}'


print(pos_only(1))
#> a=1 b=2
print(pos_only(1, 2))
#> a=1 b=2


@validate_arguments
def var_args(*args: int) -> str:
    return str(args)


print(var_args(1))
#> (1,)
print(var_args(1, 2))
#> (1, 2)
print(var_args(1, 2, 3))
#> (1, 2, 3)


@validate_arguments
def var_kwargs(**kwargs: int) -> str:
    return str(kwargs)


print(var_kwargs(a=1))
#> {'a': 1}
print(var_kwargs(a=1, b=2))
#> {'a': 1, 'b': 2}


@validate_arguments
def armageddon(
    a: int,
    /,  # python 3.8 only
    b: int,
    c: int = None,
    *d: int,
    e: int,
    f: int = None,
    **g: int,
) -> str:
    return f'a={a} b={b} c={c} d={d} e={e} f={f} g={g}'


print(armageddon(1, 2, e=3))
#> a=1 b=2 c=None d=() e=3 f=None g={}
print(armageddon(1, 2, 3, 4, 5, 6, e=8, f=9, g=10, spam=11))
#> a=1 b=2 c=3 d=(4, 5, 6) e=8 f=9 g={'g': 10, 'spam': 11}
```

## Using Field to describe function arguments

[Field](schema.md#field-customization) can also be used with `validate_arguments` to provide extra information about
the field and validations. In general it should be used in a type hint with
[Annotated](schema.md#typingannotated-fields), unless `default_factory` is specified, in which case it should be used
as the default value of the field:

```py
from datetime import datetime

from typing_extensions import Annotated

from pydantic import Field, ValidationError, validate_arguments


@validate_arguments
def how_many(num: Annotated[int, Field(gt=10)]):
    return num


try:
    how_many(1)
except ValidationError as e:
    print(e)
    """
    1 validation error for HowMany
    num
      Input should be greater than 10 [type=greater_than, input_value=1, input_type=int]
    """


@validate_arguments
def when(dt: datetime = Field(default_factory=datetime.now)):
    return dt


print(type(when()))
#> <class 'datetime.datetime'>
```

The [alias](model_config.md#alias-precedence) can be used with the decorator as normal.

```py
from typing_extensions import Annotated

from pydantic import Field, validate_arguments


@validate_arguments
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num


how_many(number=42)
```


## Usage with mypy

The `validate_arguments` decorator should work "out of the box" with [mypy](http://mypy-lang.org/) since it's
defined to return a function with the same signature as the function it decorates. The only limitation is that
since we trick mypy into thinking the function returned by the decorator is the same as the function being
decorated; access to the [raw function](#raw-function) or other attributes will require `type: ignore`.

## Validate without calling the function

By default, arguments validation is done by directly calling the decorated function with parameters.
But what if you wanted to validate them without *actually* calling the function?
To do that you can call the `validate` method bound to the decorated function.

```py
from pydantic import ValidationError, validate_arguments


@validate_arguments
def slow_sum(a: int, b: int) -> int:
    print(f'Called with a={a}, b={b}')
    #> Called with a=1, b=1
    return a + b


slow_sum(1, 1)

slow_sum.validate(2, 2)

try:
    slow_sum.validate(1, 'b')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for SlowSum
    b
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='b', input_type=str]
    """
```

## Raw function

The raw function which was decorated is accessible, this is useful if in some scenarios you trust your input
arguments and want to call the function in the most performant way (see [notes on performance](#performance) below):

```py
from pydantic import validate_arguments


@validate_arguments
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

## Async Functions

`validate_arguments` can also be used on async functions:

```py
class Connection:
    async def execute(self, sql, *args):
        return 'testing@example.com'


conn = Connection()
# ignore-above
import asyncio

from pydantic import PositiveInt, ValidationError, validate_arguments


@validate_arguments
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
                'loc': ('user_id',),
                'msg': 'Input should be greater than 0',
                'input': -4,
                'ctx': {'gt': 0},
            }
        ]
        """


asyncio.run(main())
# requires: `conn.execute()` that will return `'testing@example.com'`
```

## Custom Config

The model behind `validate_arguments` can be customised using a config setting which is equivalent to
setting the `Config` sub-class in normal models.

!!! warning
    The `fields` and `alias_generator` properties of `Config` which allow aliases to be configured are not supported
    yet with `@validate_arguments`, using them will raise an error.

Configuration is set using the `config` keyword argument to the decorator, it may be either a config class
or a dict of properties which are converted to a class later.

```py
from pydantic import ValidationError, validate_arguments


class Foobar:
    def __init__(self, v: str):
        self.v = v

    def __add__(self, other: 'Foobar') -> str:
        return f'{self} + {other}'

    def __str__(self) -> str:
        return f'Foobar({self.v})'


@validate_arguments(config=dict(arbitrary_types_allowed=True))
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
    2 validation errors for AddFoobars
    a
      Input should be an instance of Foobar [type=is_instance_of, input_value=1, input_type=int]
    b
      Input should be an instance of Foobar [type=is_instance_of, input_value=2, input_type=int]
    """
```

## Limitations

`validate_arguments` has been released on a provisional basis without all the bells and whistles, which may
be added later, see [#1205](https://github.com/pydantic/pydantic/issues/1205) for some more discussion of this.

In particular:

### Validation Exception

Currently upon validation failure, a standard *pydantic* `ValidationError` is raised,
see [model error handling](models.md#error-handling).

This is helpful since it's `str()` method provides useful details of the error which occurred and methods like
`.errors()` and `.json()` can be useful when exposing the errors to end users, however `ValidationError` inherits
from `ValueError` **not** `TypeError` which may be unexpected since Python would raise a `TypeError` upon invalid
or missing arguments. This may be addressed in future by either allow a custom error or raising a different
exception by default, or both.

### Coercion and Strictness

*pydantic* currently leans on the side of trying to coerce types rather than raise an error if a type is wrong,
see [model data conversion](models.md#data-conversion) and `validate_arguments` is no different.

See [#1098](https://github.com/pydantic/pydantic/issues/1098) and other issues with the "strictness" label
for a discussion of this. If *pydantic* gets a "strict" mode in future, `validate_arguments` will have an option
to use this, it may even become the default for the decorator.

### Performance

We've made a big effort to make *pydantic* as performant as possible
and argument inspect and model creation is only performed once when the function is defined, however
there will still be a performance impact to using the `validate_arguments` decorator compared to
calling the raw function.

In many situations this will have little or no noticeable effect, however be aware that
`validate_arguments` is not an equivalent or alternative to function definitions in strongly typed languages;
it never will be.

### Return Value

The return value of the function is not validated against its return type annotation, this may be added as an option
in future.

### Config and Validators

`fields` and `alias_generator` on custom [`Config`](model_config.md) are not supported, see [above](#custom-config).

Neither are [validators](validators.md).

### Model fields and reserved arguments

The following names may not be used by arguments since they can be used internally to store information about
the function's signature:

* `v__args`
* `v__kwargs`
* `v__positional_only`

These names (together with `"args"` and `"kwargs"`) may or may not (depending on the function's signature) appear as
fields on the internal *pydantic* model accessible via `.model` thus this model isn't especially useful
(e.g. for generating a schema) at the moment.

This should be fixable in future as the way error are raised is changed.
