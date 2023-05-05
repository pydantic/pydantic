---
description: Support for iterable types.
---

`typing.Sequence`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Iterable`
: this is reserved for iterables that shouldn't be consumed. See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation

*pydantic* uses standard library `typing` types as defined in PEP 484 to define complex objects.

```py
from typing import Deque, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from pydantic import BaseModel


class Model(BaseModel):
    simple_list: list = None
    list_of_ints: List[int] = None

    simple_tuple: tuple = None
    tuple_of_different_types: Tuple[int, float, str, bool] = None

    simple_dict: dict = None
    dict_str_float: Dict[str, float] = None

    simple_set: set = None
    set_bytes: Set[bytes] = None
    frozen_set: FrozenSet[int] = None

    str_or_bytes: Union[str, bytes] = None
    none_or_str: Optional[str] = None

    sequence_of_ints: Sequence[int] = None

    compound: Dict[Union[str, bytes], List[Set[int]]] = None

    deque: Deque[int] = None


print(Model(simple_list=['1', '2', '3']).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
#> [1, 2, 3]

print(Model(simple_dict={'a': 1, b'b': 2}).simple_dict)
#> {'a': 1, b'b': 2}
print(Model(dict_str_float={'a': 1, b'b': 2}).dict_str_float)
#> {'a': 1.0, 'b': 2.0}

print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
#> (1, 2, 3, 4)
print(Model(tuple_of_different_types=[4, 3, '2', 1]).tuple_of_different_types)
#> (4, 3.0, '2', True)

print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)

print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

### Strings aren't Sequences


*pydantic* doesn't treat strings, i.e. `str` and `bytes` subclasses, as sequences:

```py
from typing import Optional, Sequence

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    sequence_of_strs: Optional[Sequence[str]] = None
    sequence_of_bytes: Optional[Sequence[bytes]] = None


print(Model(sequence_of_strs=['a', 'bc']).sequence_of_strs)
#> ['a', 'bc']
print(Model(sequence_of_strs=('a', 'bc')).sequence_of_strs)
#> ('a', 'bc')
print(Model(sequence_of_bytes=[b'a', b'bc']).sequence_of_bytes)
#> [b'a', b'bc']
print(Model(sequence_of_bytes=(b'a', b'bc')).sequence_of_bytes)
#> (b'a', b'bc')


try:
    Model(sequence_of_strs='abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_strs
      'str' instances are not allowed as a Sequence value [type=sequence_str, input_value='abc', input_type=str]
    """
try:
    Model(sequence_of_bytes=b'abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_bytes
      'bytes' instances are not allowed as a Sequence value [type=sequence_str, input_value=b'abc', input_type=bytes]
    """
```


## Infinite Generators

If you have a generator you can use `Sequence` as described above. In that case, the
generator will be consumed and stored on the model as a list and its values will be
validated with the sub-type of `Sequence` (e.g. `int` in `Sequence[int]`).

But if you have a generator that you don't want to be consumed, e.g. an infinite
generator or a remote data loader, you can define its type with `Iterable`:

```py
from typing import Iterable

from pydantic import BaseModel


class Model(BaseModel):
    infinite: Iterable[int]


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)
"""
infinite=ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))
"""

for i in m.infinite:
    print(i)
    #> 0
    #> 1
    #> 2
    #> 3
    #> 4
    #> 5
    #> 6
    #> 7
    #> 8
    #> 9
    #> 10
    if i == 10:
        break
```

!!! warning
    `Iterable` fields only perform a simple check that the argument is iterable and
    won't be consumed.

    No validation of their values is performed as it cannot be done without consuming
    the iterable.

!!! tip
    If you want to validate the values of an infinite generator you can create a
    separate model and use it while consuming the generator, reporting the validation
    errors as appropriate.

    pydantic can't validate the values automatically for you because it would require
    consuming the infinite generator.

## Validating the first value

You can create a [validator](../validators.md) to validate the first value in an infinite generator and still not consume it entirely.

```py test="xfail - what's going on here?"
import itertools
from typing import Iterable

from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    infinite: Iterable[int]

    @field_validator('infinite')
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def infinite_first_int(cls, iterable, field):
        first_value = next(iterable)
        if field.sub_fields:
            # The Iterable had a parameter type, in this case it's int
            # We use it to validate the first value
            sub_field = field.sub_fields[0]
            v, error = sub_field.validate(first_value, {}, loc='first_value')
            if error:
                raise ValidationError([error], cls)
        # This creates a new generator that returns the first value and then
        # the rest of the values from the (already started) iterable
        return itertools.chain([first_value], iterable)


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)


def infinite_strs():
    while True:
        yield from 'allthesingleladies'


try:
    Model(infinite=infinite_strs())
except ValidationError as e:
    print(e)
```
