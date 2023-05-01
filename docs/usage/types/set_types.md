`set`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a set;
  see `typing.Set` below for sub-type constraints

`frozenset`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a frozen set;
  see `typing.FrozenSet` below for sub-type constraints

`deque`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a deque;
  see `typing.Deque` below for sub-type constraints

`typing.Set`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.FrozenSet`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Deque`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

## Constrained Types

The value of numerous common types can be restricted using `con*` type functions:

`conset`
: type method for constraining sets;
  see [Constrained Types](#constrained-types)

`confrozenset`
: type method for constraining frozen sets;
  see [Constrained Types](#constrained-types)

### Arguments to `conset`
The following arguments are available when using the `conset` type function

- `item_type: Type[T]`: type of the set items
- `min_items: int = None`: minimum number of items in the set
- `max_items: int = None`: maximum number of items in the set

### Arguments to `confrozenset`
The following arguments are available when using the `confrozenset` type function

- `item_type: Type[T]`: type of the frozenset items
- `min_items: int = None`: minimum number of items in the frozenset
- `max_items: int = None`: maximum number of items in the frozenset
