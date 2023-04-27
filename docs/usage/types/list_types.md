`list`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a list;
  see `typing.List` below for sub-type constraints

`tuple`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a tuple;
  see `typing.Tuple` below for sub-type constraints

`typing.List`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Tuple`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`subclass of typing.NamedTuple`
: Same as `tuple` but instantiates with the given namedtuple and validates fields since they are annotated.
  See [Annotated Types](#annotated-types) below for more detail on parsing and validation

`subclass of collections.namedtuple`
: Same as `subclass of typing.NamedTuple` but all fields will have type `Any` since they are not annotated

### Typing Iterables

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
```

### NamedTuple

```py
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    p.0
      Input should be a valid integer, got a number with a fractional part [type=int_from_float, input_value='1.3', input_type=str]
    """
```
