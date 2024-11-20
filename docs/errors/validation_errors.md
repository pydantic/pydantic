Pydantic attempts to provide useful validation errors. Below are details on common validation errors users
may encounter when working with pydantic, together with some suggestions on how to fix them.

## `arguments_type`

This error is raised when an object that would be passed as arguments to a function during validation is not
a `tuple`, `list`, or `dict`. Because `NamedTuple` uses function calls in its implementation, that is one way to
produce this error:

```python
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class MyNamedTuple(NamedTuple):
    x: int


class MyModel(BaseModel):
    field: MyNamedTuple


try:
    MyModel.model_validate({'field': 'invalid'})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'arguments_type'
```

## `assertion_error`

This error is raised when a failing `assert` statement is encountered during validation:

```python
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    @classmethod
    def force_x_positive(cls, v):
        assert v > 0
        return v


try:
    Model(x=-1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'assertion_error'
```

## `bool_parsing`

This error is raised when the input value is a string that is not valid for coercion to a boolean:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bool


Model(x='true')  # OK

try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bool_parsing'
```

## `bool_type`

This error is raised when the input value's type is not valid for a `bool` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bool


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bool_type'
```

## `bytes_invalid_encoding`

This error is raised when a `bytes` value is invalid under the configured encoding.
In the following example, `b'a'` is invalid hex (odd number of digits).

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bytes
    model_config = {'val_json_bytes': 'hex'}


try:
    Model(x=b'a')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_invalid_encoding'
```

This error is also raised for strict fields when the input value is not an instance of `bool`.

## `bytes_too_long`

This error is raised when the length of a `bytes` value is greater than the field's `max_length` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: bytes = Field(max_length=3)


try:
    Model(x=b'test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_too_long'
```

## `bytes_too_short`

This error is raised when the length of a `bytes` value is less than the field's `min_length` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: bytes = Field(min_length=3)


try:
    Model(x=b't')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_too_short'
```

## `bytes_type`

This error is raised when the input value's type is not valid for a `bytes` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bytes


try:
    Model(x=123)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_type'
```

This error is also raised for strict fields when the input value is not an instance of `bytes`.

## `callable_type`

This error is raised when the input value is not valid as a `Callable`:

```python
from typing import Any, Callable

from pydantic import BaseModel, ImportString, ValidationError


class Model(BaseModel):
    x: ImportString[Callable[[Any], Any]]


Model(x='math:cos')  # OK

try:
    Model(x='os.path')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'callable_type'
```

## `complex_str_parsing`

This error is raised when the input value is a string but cannot be parsed as a complex number because
it does not follow the [rule](https://docs.python.org/3/library/functions.html#complex) in Python:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    num: complex


try:
    # Complex numbers in json are expected to be valid complex strings.
    # This value `abc` is not a valid complex string.
    Model.model_validate_json('{"num": "abc"}')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'complex_str_parsing'
```

## `complex_type`

This error is raised when the input value cannot be interpreted as a complex number:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    num: complex


try:
    Model(num=False)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'complex_type'
```

## `dataclass_exact_type`

This error is raised when validating a dataclass with `strict=True` and the input is not an instance of the dataclass:

```python
import pydantic.dataclasses
from pydantic import TypeAdapter, ValidationError


@pydantic.dataclasses.dataclass
class MyDataclass:
    x: str


adapter = TypeAdapter(MyDataclass)

print(adapter.validate_python(MyDataclass(x='test'), strict=True))
#> MyDataclass(x='test')
print(adapter.validate_python({'x': 'test'}))
#> MyDataclass(x='test')

try:
    adapter.validate_python({'x': 'test'}, strict=True)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'dataclass_exact_type'
```

## `dataclass_type`

This error is raised when the input value is not valid for a `dataclass` field:

```python
from pydantic import ValidationError, dataclasses


@dataclasses.dataclass
class Inner:
    x: int


@dataclasses.dataclass
class Outer:
    y: Inner


Outer(y=Inner(x=1))  # OK

try:
    Outer(y=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'dataclass_type'
```

## `date_from_datetime_inexact`

This error is raised when the input `datetime` value provided for a `date` field has a nonzero time component.
For a timestamp to parse into a field of type `date`, the time components must all be zero:

```python
from datetime import date, datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


Model(x='2023-01-01')  # OK
Model(x=datetime(2023, 1, 1))  # OK

try:
    Model(x=datetime(2023, 1, 1, 12))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_from_datetime_inexact'
```

## `date_from_datetime_parsing`

This error is raised when the input value is a string that cannot be parsed for a `date` field:

```python
from datetime import date

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


try:
    Model(x='XX1494012000')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_from_datetime_parsing'
```

## `date_future`

This error is raised when the input value provided for a `FutureDate` field is not in the future:

```python
from datetime import date

from pydantic import BaseModel, FutureDate, ValidationError


class Model(BaseModel):
    x: FutureDate


try:
    Model(x=date(2000, 1, 1))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_future'
```

## `date_parsing`

This error is raised when validating JSON where the input value is string that cannot be parsed for a `date` field:

```python
import json
from datetime import date

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: date = Field(strict=True)


try:
    Model.model_validate_json(json.dumps({'x': '1'}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_parsing'
```

## `date_past`

This error is raised when the value provided for a `PastDate` field is not in the past:

```python
from datetime import date, timedelta

from pydantic import BaseModel, PastDate, ValidationError


class Model(BaseModel):
    x: PastDate


try:
    Model(x=date.today() + timedelta(1))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_past'
```

## `date_type`

This error is raised when the input value's type is not valid for a `date` field:

```python
from datetime import date

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_type'
```

This error is also raised for strict fields when the input value is not an instance of `date`.

## `datetime_from_date_parsing`

!!! note
    Support for this error, along with support for parsing datetimes from `yyyy-MM-DD` dates will be added in `v2.6.0`

This error is raised when the input value is a string that cannot be parsed for a `datetime` field:

```python
from datetime import datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: datetime


try:
    # there is no 13th month
    Model(x='2023-13-01')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_from_date_parsing'
```

## `datetime_future`

This error is raised when the value provided for a `FutureDatetime` field is not in the future:

```python
from datetime import datetime

from pydantic import BaseModel, FutureDatetime, ValidationError


class Model(BaseModel):
    x: FutureDatetime


try:
    Model(x=datetime(2000, 1, 1))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_future'
```

## `datetime_object_invalid`

This error is raised when something about the `datetime` object is not valid:

```python
from datetime import datetime, tzinfo

from pydantic import AwareDatetime, BaseModel, ValidationError


class CustomTz(tzinfo):
    # utcoffset is not implemented!

    def tzname(self, _dt):
        return 'CustomTZ'


class Model(BaseModel):
    x: AwareDatetime


try:
    Model(x=datetime(2023, 1, 1, tzinfo=CustomTz()))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_object_invalid'
```

## `datetime_parsing`

This error is raised when the value is a string that cannot be parsed for a `datetime` field:

```python
import json
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: datetime = Field(strict=True)


try:
    Model.model_validate_json(json.dumps({'x': 'not a datetime'}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_parsing'
```

## `datetime_past`

This error is raised when the value provided for a `PastDatetime` field is not in the past:

```python
from datetime import datetime, timedelta

from pydantic import BaseModel, PastDatetime, ValidationError


class Model(BaseModel):
    x: PastDatetime


try:
    Model(x=datetime.now() + timedelta(100))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_past'
```

## `datetime_type`

This error is raised when the input value's type is not valid for a `datetime` field:

```python
from datetime import datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: datetime


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_type'
```

This error is also raised for strict fields when the input value is not an instance of `datetime`.

## `decimal_max_digits`

This error is raised when the value provided for a `Decimal` has too many digits:

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(max_digits=3)


try:
    Model(x='42.1234')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_max_digits'
```

## `decimal_max_places`

This error is raised when the value provided for a `Decimal` has too many digits after the decimal point:

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(decimal_places=3)


try:
    Model(x='42.1234')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_max_places'
```

## `decimal_parsing`

This error is raised when the value provided for a `Decimal` could not be parsed as a decimal number:

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(decimal_places=3)


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_parsing'
```

## `decimal_type`

This error is raised when the value provided for a `Decimal` is of the wrong type:

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(decimal_places=3)


try:
    Model(x=[1, 2, 3])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_type'
```

This error is also raised for strict fields when the input value is not an instance of `Decimal`.

## `decimal_whole_digits`

This error is raised when the value provided for a `Decimal` has more digits before the decimal point than `max_digits` - `decimal_places` (as long as both are specified):

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(max_digits=6, decimal_places=3)


try:
    Model(x='12345.6')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_whole_digits'
```

This error is also raised for strict fields when the input value is not an instance of `Decimal`.

## `dict_type`

This error is raised when the input value's type is not `dict` for a `dict` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict


try:
    Model(x=['1', '2'])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'dict_type'
```

## `enum`

This error is raised when the input value does not exist in an `enum` field members:

```python
from enum import Enum

from pydantic import BaseModel, ValidationError


class MyEnum(str, Enum):
    option = 'option'


class Model(BaseModel):
    x: MyEnum


try:
    Model(x='other_option')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'enum'
```

## `extra_forbidden`

This error is raised when the input value contains extra fields, but `model_config['extra'] == 'forbid'`:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: str

    model_config = ConfigDict(extra='forbid')


try:
    Model(x='test', y='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'extra_forbidden'
```

You can read more about the `extra` configuration in the [Extra Attributes][pydantic.config.ConfigDict.extra] section.

## `finite_number`

This error is raised when the value is infinite, or too large to be represented as a 64-bit floating point number
during validation:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=2.2250738585072011e308)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'finite_number'
```

## `float_parsing`

This error is raised when the value is a string that can't be parsed as a `float`:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: float


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'float_parsing'
```

## `float_type`

This error is raised when the input value's type is not valid for a `float` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: float


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'float_type'
```

## `frozen_field`

This error is raised when you attempt to assign a value to a field with `frozen=True`, or to delete such a field:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field('test', frozen=True)


model = Model()

try:
    model.x = 'test1'
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_field'

try:
    del model.x
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_field'
```

## `frozen_instance`

This error is raised when `model_config['frozen] == True` and you attempt to delete or assign a new value to
any of the fields:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(frozen=True)


m = Model(x=1)

try:
    m.x = 2
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_instance'

try:
    del m.x
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_instance'
```

## `frozen_set_type`

This error is raised when the input value's type is not valid for a `frozenset` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: frozenset


try:
    model = Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_set_type'
```

## `get_attribute_error`

This error is raised when `model_config['from_attributes'] == True` and an error is raised while reading the attributes:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Foobar:
    def __init__(self):
        self.x = 1

    @property
    def y(self):
        raise RuntimeError('intentional error')


class Model(BaseModel):
    x: int
    y: str

    model_config = ConfigDict(from_attributes=True)


try:
    Model.model_validate(Foobar())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'get_attribute_error'
```

## `greater_than`

This error is raised when the value is not greater than the field's `gt` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(gt=10)


try:
    Model(x=10)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'greater_than'
```

## `greater_than_equal`

This error is raised when the value is not greater than or equal to the field's `ge` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(ge=10)


try:
    Model(x=9)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'greater_than_equal'
```

## `int_from_float`

This error is raised when you provide a `float` value for an `int` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=0.5)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_from_float'
```

## `int_parsing`

This error is raised when the value can't be parsed as `int`:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_parsing'
```

## `int_parsing_size`

This error is raised when attempting to parse a python or JSON value from a string outside the maximum range that Python
`str` to `int` parsing permits:

```python
import json

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


# from Python
assert Model(x='1' * 4_300).x == int('1' * 4_300)  # OK

too_long = '1' * 4_301
try:
    Model(x=too_long)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_parsing_size'

# from JSON
try:
    Model.model_validate_json(json.dumps({'x': too_long}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_parsing_size'
```

## `int_type`

This error is raised when the input value's type is not valid for an `int` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_type'
```

## `invalid_key`

This error is raised when attempting to validate a `dict` that has a key that is not an instance of `str`:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')


try:
    Model.model_validate({'x': 1, b'y': 2})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'invalid_key'
```

## `is_instance_of`

This error is raised when the input value is not an instance of the expected type:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Nested:
    x: str


class Model(BaseModel):
    y: Nested

    model_config = ConfigDict(arbitrary_types_allowed=True)


try:
    Model(y='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'is_instance_of'
```

## `is_subclass_of`

This error is raised when the input value is not a subclass of the expected type:

```python
from typing import Type

from pydantic import BaseModel, ValidationError


class Nested:
    x: str


class Model(BaseModel):
    y: Type[Nested]


try:
    Model(y='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'is_subclass_of'
```

## `iterable_type`

This error is raised when the input value is not valid as an `Iterable`:

```python
from typing import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    y: Iterable


try:
    Model(y=123)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'iterable_type'
```

## `iteration_error`

This error is raised when an error occurs during iteration:

```python
from typing import List

from pydantic import BaseModel, ValidationError


def gen():
    yield 1
    raise RuntimeError('error')


class Model(BaseModel):
    x: List[int]


try:
    Model(x=gen())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'iteration_error'
```

## `json_invalid`

This error is raised when the input value is not a valid JSON string:

```python
from pydantic import BaseModel, Json, ValidationError


class Model(BaseModel):
    x: Json


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'json_invalid'
```

## `json_type`

This error is raised when the input value is of a type that cannot be parsed as JSON:

```python
from pydantic import BaseModel, Json, ValidationError


class Model(BaseModel):
    x: Json


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'json_type'
```

## `less_than`

This error is raised when the input value is not less than the field's `lt` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(lt=10)


try:
    Model(x=10)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'less_than'
```

## `less_than_equal`

This error is raised when the input value is not less than or equal to the field's `le` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(le=10)


try:
    Model(x=11)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'less_than_equal'
```

## `list_type`

This error is raised when the input value's type is not valid for a `list` field:

```python
from typing import List

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: List[int]


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'list_type'
```

## `literal_error`

This error is raised when the input value is not one of the expected literal values:

```python
from typing import Literal

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Literal['a', 'b']


Model(x='a')  # OK

try:
    Model(x='c')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'literal_error'
```

## `mapping_type`

This error is raised when a problem occurs during validation due to a failure in a call to the methods from the
`Mapping` protocol, such as `.items()`:

```python
from collections.abc import Mapping
from typing import Dict

from pydantic import BaseModel, ValidationError


class BadMapping(Mapping):
    def items(self):
        raise ValueError()

    def __iter__(self):
        raise ValueError()

    def __getitem__(self, key):
        raise ValueError()

    def __len__(self):
        return 1


class Model(BaseModel):
    x: Dict[str, str]


try:
    Model(x=BadMapping())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'mapping_type'
```

## `missing`

This error is raised when there are required fields missing from the input value:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing'
```

## `missing_argument`

This error is raised when a required positional-or-keyword argument is not passed to a function decorated with
`validate_call`:

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int):
    return a


try:
    foo()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_argument'
```

## `missing_keyword_only_argument`

This error is raised when a required keyword-only argument is not passed to a function decorated with `validate_call`:

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(*, a: int):
    return a


try:
    foo()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_keyword_only_argument'
```

## `missing_positional_only_argument`

This error is raised when a required positional-only argument is not passed to a function decorated with
`validate_call`:

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int, /):
    return a


try:
    foo()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_positional_only_argument'
```

## `model_attributes_type`

This error is raised when the input value is not a valid dictionary, model instance, or instance that fields can be extracted from:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int


# simply validating a dict
print(Model.model_validate({'a': 1, 'b': 2}))
#> a=1 b=2


class CustomObj:
    def __init__(self, a, b):
        self.a = a
        self.b = b


# using from attributes to extract fields from an objects
print(Model.model_validate(CustomObj(3, 4), from_attributes=True))
#> a=3 b=4

try:
    Model.model_validate('not an object', from_attributes=True)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'model_attributes_type'
```

## `model_type`

This error is raised when the input to a model is not an instance of the model or dict:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int


# simply validating a dict
m = Model.model_validate({'a': 1, 'b': 2})
print(m)
#> a=1 b=2

# validating an existing model instance
print(Model.model_validate(m))
#> a=1 b=2

try:
    Model.model_validate('not an object')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'model_type'
```

## `multiple_argument_values`

This error is raised when you provide multiple values for a single argument while calling a function decorated with
`validate_call`:

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int):
    return a


try:
    foo(1, a=2)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'multiple_argument_values'
```

## `multiple_of`

This error is raised when the input is not a multiple of a field's `multiple_of` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(multiple_of=5)


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'multiple_of'
```

## `needs_python_object`

This type of error is raised when validation is attempted from a format that cannot be converted to a Python object.
For example, we cannot check `isinstance` or `issubclass` from JSON:

```python
import json
from typing import Type

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    bm: Type[BaseModel]


try:
    Model.model_validate_json(json.dumps({'bm': 'not a basemodel class'}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'needs_python_object'
```

## `no_such_attribute`

This error is raised when `validate_assignment=True` in the config, and you attempt to assign a value to an attribute
that is not an existing field:

```python
from pydantic import ConfigDict, ValidationError, dataclasses


@dataclasses.dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass:
    x: int


m = MyDataclass(x=1)
try:
    m.y = 10
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'no_such_attribute'
```

## `none_required`

This error is raised when the input value is not `None` for a field that requires `None`:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: None


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'none_required'
```

!!! note
    You may encounter this error when there is a naming collision in your model between a field name and its type. More specifically, this error is likely to be thrown when the default value of that field is `None`.

    For example, the following would yield the `none_required` validation error since the field `int` is set to a default value of `None` and has the exact same name as its type, which causes problems with validation.

    ```python {test="skip"}
    from typing import Optional

    from pydantic import BaseModel


    class M1(BaseModel):
        int: Optional[int] = None


    m = M1(int=123)  # errors
    ```

## `recursion_loop`

This error is raised when a cyclic reference is detected:

```python
from typing import List

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: List['Model']


d = {'x': []}
d['x'].append(d)
try:
    Model(**d)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'recursion_loop'
```

## `set_type`

This error is raised when the value type is not valid for a `set` field:

```python
from typing import Set

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Set[int]


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'set_type'
```

## `string_pattern_mismatch`

This error is raised when the input value doesn't match the field's `pattern` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(pattern='test')


try:
    Model(x='1')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_pattern_mismatch'
```

## `string_sub_type`

This error is raised when the value is an instance of a strict subtype of `str` when the field is strict:

```python
from enum import Enum

from pydantic import BaseModel, Field, ValidationError


class MyEnum(str, Enum):
    foo = 'foo'


class Model(BaseModel):
    x: str = Field(strict=True)


try:
    Model(x=MyEnum.foo)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_sub_type'
```

## `string_too_long`

This error is raised when the input value is a string whose length is greater than the field's `max_length` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(max_length=3)


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_too_long'
```

## `string_too_short`

This error is raised when the input value is a string whose length is less than the field's `min_length` constraint:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(min_length=3)


try:
    Model(x='t')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_too_short'
```

## `string_type`

This error is raised when the input value's type is not valid for a `str` field:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_type'
```

This error is also raised for strict fields when the input value is not an instance of `str`.

## `string_unicode`

This error is raised when the value cannot be parsed as a Unicode string:

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model(x=b'\x81')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_unicode'
```

## `time_delta_parsing`

This error is raised when the input value is a string that cannot be parsed for a `timedelta` field:

```python
from datetime import timedelta

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: timedelta


try:
    Model(x='t')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_delta_parsing'
```

## `time_delta_type`

This error is raised when the input value's type is not valid for a `timedelta` field:

```python
from datetime import timedelta

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: timedelta


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_delta_type'
```

This error is also raised for strict fields when the input value is not an instance of `timedelta`.

## `time_parsing`

This error is raised when the input value is a string that cannot be parsed for a `time` field:

```python
from datetime import time

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: time


try:
    Model(x='25:20:30.400')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_parsing'
```

## `time_type`

This error is raised when the value type is not valid for a `time` field:

```python
from datetime import time

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: time


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_type'
```

This error is also raised for strict fields when the input value is not an instance of `time`.

## `timezone_aware`

This error is raised when the `datetime` value provided for a timezone-aware `datetime` field
doesn't have timezone information:

```python
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ValidationError


class Model(BaseModel):
    x: AwareDatetime


try:
    Model(x=datetime.now())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'timezone_aware'
```

## `timezone_naive`

This error is raised when the `datetime` value provided for a timezone-naive `datetime` field
has timezone info:

```python
from datetime import datetime, timezone

from pydantic import BaseModel, NaiveDatetime, ValidationError


class Model(BaseModel):
    x: NaiveDatetime


try:
    Model(x=datetime.now(tz=timezone.utc))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'timezone_naive'
```

## `too_long`

This error is raised when the input value's length is greater than the field's `max_length` constraint:

```python
from typing import List

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: List[int] = Field(max_length=3)


try:
    Model(x=[1, 2, 3, 4])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'too_long'
```

## `too_short`

This error is raised when the value length is less than the field's `min_length` constraint:

```python
from typing import List

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: List[int] = Field(min_length=3)


try:
    Model(x=[1, 2])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'too_short'
```

## `tuple_type`

This error is raised when the input value's type is not valid for a `tuple` field:

```python
from typing import Tuple

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Tuple[int]


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'tuple_type'
```

This error is also raised for strict fields when the input value is not an instance of `tuple`.

## `unexpected_keyword_argument`

This error is raised when you provide a value by keyword for a positional-only
argument while calling a function decorated with `validate_call`:

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int, /):
    return a


try:
    foo(a=2)
except ValidationError as exc:
    print(repr(exc.errors()[1]['type']))
    #> 'unexpected_keyword_argument'
```

It is also raised when using pydantic.dataclasses and `extra=forbid`:

```python
from pydantic import TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass


@dataclass(config={'extra': 'forbid'})
class Foo:
    bar: int


try:
    TypeAdapter(Foo).validate_python({'bar': 1, 'foobar': 2})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'unexpected_keyword_argument'
```

## `unexpected_positional_argument`

This error is raised when you provide a positional value for a keyword-only
argument while calling a function decorated with `validate_call`:

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(*, a: int):
    return a


try:
    foo(2)
except ValidationError as exc:
    print(repr(exc.errors()[1]['type']))
    #> 'unexpected_positional_argument'
```

## `union_tag_invalid`

This error is raised when the input's discriminator is not one of the expected values:

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(discriminator='pet_type')


try:
    Model(cat={'pet_type': 'dog'})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'union_tag_invalid'
```

## `union_tag_not_found`

This error is raised when it is not possible to extract a discriminator value from the input:

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(discriminator='pet_type')


try:
    Model(cat={'name': 'blackcat'})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'union_tag_not_found'
```

## `url_parsing`

This error is raised when the input value cannot be parsed as a URL:

```python
from pydantic import AnyUrl, BaseModel, ValidationError


class Model(BaseModel):
    x: AnyUrl


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_parsing'
```

## `url_scheme`

This error is raised when the URL scheme is not valid for the URL type of the field:

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x='ftp://example.com')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_scheme'
```

## `url_syntax_violation`

This error is raised when the URL syntax is not valid:

```python
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl = Field(strict=True)


try:
    Model(x='http:////example.com')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_syntax_violation'
```

## `url_too_long`

This error is raised when the URL length is greater than 2083:

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x='x' * 2084)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_too_long'
```

## `url_type`

This error is raised when the input value's type is not valid for a URL field:

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_type'
```

## `uuid_parsing`

This error is raised when the input value's type is not valid for a UUID field:

```python
from uuid import UUID

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    u: UUID


try:
    Model(u='12345678-124-1234-1234-567812345678')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'uuid_parsing'
```

## `uuid_type`

This error is raised when the input value's type is not valid instance for a UUID field (str, bytes or UUID):

```python
from uuid import UUID

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    u: UUID


try:
    Model(u=1234567812412341234567812345678)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'uuid_type'
```

## `uuid_version`

This error is raised when the input value's type is not match UUID version:

```python
from pydantic import UUID5, BaseModel, ValidationError


class Model(BaseModel):
    u: UUID5


try:
    Model(u='a6cc5730-2261-11ee-9c43-2eb5a363657c')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'uuid_version'
```

## `value_error`

This error is raised when a `ValueError` is raised during validation:

```python
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    x: str

    @field_validator('x')
    @classmethod
    def repeat_b(cls, v):
        raise ValueError()


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'value_error'
```
