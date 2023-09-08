# Bytes and ByteSize

`bytes`
: `bytes` are accepted as-is, `bytearray` is converted using `bytes(v)`, and `str` is converted using `v.encode()`.

`SecretBytes`
: Like `bytes`, but where the value is kept partially secret.

`ByteSize`
: Converts a string representing a number of bytes with units (such as `'1KB'` or `'11.5MiB'`) into an integer.

`conbytes`
: A function which returns a type that can be used to add constraints to `bytes`.

### Arguments to `conbytes`
The following arguments are available when using the `conbytes` type function

- `min_length: int = None`: minimum length of the byte string
- `max_length: int = None`: maximum length of the byte string
- `strict: bool = False`: controls type coercion

However, for the sake of improved integration with type checkers, we now discourage the use of `conbytes` and other
function calls used to return constrained types. Instead, you can use `pydantic.types.Strict` and `annotated_types.Len`
as annotations to achieve these constraints:

```py
import annotated_types
from typing_extensions import Annotated

from pydantic import BaseModel, Strict


class MyModel(BaseModel):
    # Instead of `my_bytes: conbytes(strict=True, min_length=10, max_length=20)`, use:
    my_bytes: Annotated[bytes, Strict(), annotated_types.Len(10, 20)]
```


## Using ByteSize

You can use the `ByteSize` data type to (case-insensitively) convert a string representation of a number of bytes into
an integer, and also to print out human-readable strings representing a number of bytes.

In conformance with [IEC 80000-13 Standard](https://en.wikipedia.org/wiki/ISO/IEC_80000) we interpret `'1KB'` to mean 1000 bytes, and `'1KiB'` to mean 1024 bytes. In general, including a middle `'i'`
will cause the unit to be interpreted as a power of 2, rather than a power of 10 (so, for example,
`'1 MB'` is treated as `1_000_000` bytes, whereas `'1 MiB'` is treated as `1_048_576` bytes).

!!! info
    Note that `1b` will be parsed as "1 byte" and not "1 bit".

```py
from pydantic import BaseModel, ByteSize


class MyModel(BaseModel):
    size: ByteSize


print(MyModel(size=52000).size)
#> 52000
print(MyModel(size='3000 KiB').size)
#> 3072000

m = MyModel(size='50 PB')
print(m.size.human_readable())
#> 44.4PiB
print(m.size.human_readable(decimal=True))
#> 50.0PB

print(m.size.to('TiB'))
#> 45474.73508864641
```
