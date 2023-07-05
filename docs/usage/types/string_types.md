---
description: Useful types provided by Pydantic.
---

## str

Strings are accepted as-is, `bytes` and `bytearray` are converted using `v.decode()`,
enums inheriting from `str` are converted using `v.value`, and all other types cause an error

## EmailStr

`EmailStr` requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed.
The input string must be a valid email address, and the output is a simple string

## NameEmail

`NameEmail` requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed.
The input string must be either a valid email address or in the format `Fred Bloggs <fred.bloggs@example.com>`,
and the output is a `NameEmail` object which has two properties: `name` and `email`.
For `Fred Bloggs <fred.bloggs@example.com>` the name would be `"Fred Bloggs"`.
For `fred.bloggs@example.com` it would be `"fred.bloggs"`.

## ImportString

`ImportString` expects a string and loads the Python object importable at that dotted path.
Attributes of modules may be separated from the module by `:` or `.`, e.g. if `'math:cos'` was provided,
the resulting field value would be the function`cos`. If a `.` is used and both an attribute and submodule
are present at the same path, the module will be preferred.

On model instantiation, pointers will be evaluated and imported. There is
some nuance to this behavior, demonstrated in the examples below.

> A known limitation: setting a default value to a string
> won't result in validation (thus evaluation). This is actively
> being worked on.

**Good behavior:**
```py
from math import cos

from pydantic import BaseModel, ImportString, ValidationError


class ImportThings(BaseModel):
    obj: ImportString


# A string value will cause an automatic import
my_cos = ImportThings(obj='math.cos')

# You can use the imported function as you would expect
cos_of_0 = my_cos.obj(0)
assert cos_of_0 == 1


# A string whose value cannot be imported will raise an error
try:
    ImportThings(obj='foo.bar')
except ValidationError as e:
    print(e)
    """
    1 validation error for ImportThings
    obj
      Invalid python path: No module named 'foo.bar' [type=import_error, input_value='foo.bar', input_type=str]
    """


# Actual python objects can be assigned as well
my_cos = ImportThings(obj=cos)
my_cos_2 = ImportThings(obj='math.cos')
assert my_cos == my_cos_2
```

Serializing an `ImportString` type to json is also possible.

```py
from pydantic import BaseModel, ImportString


class ImportThings(BaseModel):
    obj: ImportString


# Create an instance
m = ImportThings(obj='math:cos')
print(m)
#> obj=<built-in function cos>
print(m.model_dump_json())
#> {"obj":"math.cos"}
```

## Constrained Types

The value of numerous common types can be restricted using `con*` type functions.

### Arguments to `constr`
The following arguments are available when using the `constr` type function

- `strip_whitespace: bool = False`: removes leading and trailing whitespace
- `to_upper: bool = False`: turns all characters to uppercase
- `to_lower: bool = False`: turns all characters to lowercase
- `strict: bool = False`: controls type coercion
- `min_length: int = None`: minimum length of the string
- `max_length: int = None`: maximum length of the string
- `pattern: str = None`: regex to validate the string against
