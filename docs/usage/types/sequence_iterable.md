---
description: Support for iterable types.
---

`typing.Sequence`
: this is intended for use when the provided value should meet the requirements of the `Sequence` protocol, and it is
  desirable to do eager validation of the values in the container. Note that when validation must be performed on the
  values of the container, the type of the container may not be preserved since validation may end up replacing values.
  We guarantee that the validated value will be a valid `typing.Sequence`, but it may have a different type than was
  provided (generally, it will become a `list`).

`typing.Iterable`
: this is intended for use when the provided value may be an iterable that shouldn't be consumed.
  See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation.
  Similar to `typing.Sequence`, we guarantee that the validated result will be a valid `typing.Iterable`,
  but it may have a different type than was provided. In particular, even if a non-generator type such as a `list`
  is provided, the post-validation value of a field of type `typing.Iterable` will be a generator.

Here is a simple example using `typing.Sequence`:

```py
from typing import Sequence

from pydantic import BaseModel


class Model(BaseModel):
    sequence_of_ints: Sequence[int] = None


print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)
```

### Strings aren't Sequences

While instances of `str` are technically valid instances of the `Sequence[str]` protocol from a type-checker's point of
view, this is frequently not intended as is a common source of bugs.

As a result, Pydantic raises a `ValidationError` if you attempt to pass a `str` or `bytes` instance into a field of type
`Sequence[str]` or `Sequence[bytes]`:

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

If you have a generator you want to validate, you can still use `Sequence` as described above.
In that case, the generator will be consumed and stored on the model as a list and its values will be
validated against the type parameter of the `Sequence` (e.g. `int` in `Sequence[int]`).

However, if you have a generator that you _don't_ want to be eagerly consumed (e.g. an infinite
generator or a remote data loader), you can use a field of type `Iterable`:

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
    During initial validation, `Iterable` fields only perform a simple check that the provided argument is iterable.
    To prevent it from being consumed, no validation of the yielded values is performed eagerly.


Though the yielded values are not validated eagerly, they are still validated when yielded, and will raise a
`ValidationError` at yield time when appropriate:

```python
from typing import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    int_iterator: Iterable[int]


def my_iterator():
    yield 13
    yield '27'
    yield 'a'


m = Model(int_iterator=my_iterator())
print(next(m.int_iterator))
#> 13
print(next(m.int_iterator))
#> 27
try:
    next(m.int_iterator)
except ValidationError as e:
    print(e)
    """
    1 validation error for ValidatorIterator
    2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```
