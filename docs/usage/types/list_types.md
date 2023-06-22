`list`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a list;
  when a generic parameter is provided, the appropriate validation is applied to all items of the list

`typing.List`
: handled the same as `list` above

`tuple`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a tuple;
  when generic parameters are provided, the appropriate validation is applied to the respective items of the tuple

`typing.Tuple`
: handled the same as `tuple` above

`deque`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a `deque`;
  when generic parameters are provided, the appropriate validation is applied to the respective items of the `deque`

`typing.Deque`
: handled the same as `deque` above

```py
from typing import Deque, List, Optional, Tuple

from pydantic import BaseModel


class Model(BaseModel):
    simple_list: Optional[list] = None
    list_of_ints: Optional[List[int]] = None

    simple_tuple: Optional[tuple] = None
    tuple_of_different_types: Optional[Tuple[int, float, bool]] = None

    deque: Optional[Deque[int]] = None


print(Model(simple_list=['1', '2', '3']).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
#> [1, 2, 3]

print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
#> (1, 2, 3, 4)
print(Model(tuple_of_different_types=[3, 2, 1]).tuple_of_different_types)
#> (3, 2.0, True)

print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

### NamedTuple

`subclasses of typing.NamedTuple`
: Similar to `tuple`, but creates instances of the given `namedtuple` class.

`types returned from collections.namedtuple`
: Similar to `subclass of typing.NamedTuple`, but since field types are not specified, all fields are treated as having
  type `Any`

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
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.3', input_type=str]
    """
```
