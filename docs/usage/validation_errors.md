Pydantic attempts to provide useful validation errors. Below are details on common validation errors users
may encounter when working with pydantic, together with some suggestions on how to fix them.

## `arguments_type`

This error is raised when arguments passed to a function are not
a tuple, list, or dictionary.

## `assertion_error`

This error is raised when a failing `assert` statement is encountered during validation.

```py
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
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'assertion_error'
```

## `bool`

This error is raised when the value type is not valid for a Boolean field.


## `bool_parsing`

This error is raised when the value is a string that is not valid for coercion to a boolean.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bool


Model(x='true')  # OK

try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'bool_parsing'
```

## `bool_type`

This error is raised when the value type is not valid for a Boolean field.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bool


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'bool_type'
```

## `bytes_too_long`

This error is raised when the length of a `bytes` value is greater than `Field.max_length`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: bytes = Field(max_length=3)


try:
    Model(x=b'test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'bytes_too_long'
```

## `bytes_too_short`

This error is raised when the length of a `bytes` value is less than `Field.min_length`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: bytes = Field(min_length=3)


try:
    Model(x=b't')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'bytes_too_short'
```

## `bytes_type`

This error is raised when the type of an input value is not valid for a `bytes` field.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bytes


try:
    Model(x=123)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'bytes_type'
```

## `callable_type`

This error is raised when the value is not a `Callable`.

```py
from typing import Any, Callable

from pydantic import BaseModel, ImportString, ValidationError


class Model(BaseModel):
    x: ImportString[Callable[[Any], Any]]


try:
    Model(x='os.path')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'callable_type'
```

Valid example:

```py
from typing import Any, Callable

from pydantic import BaseModel, ImportString


class Model(BaseModel):
    x: ImportString[Callable[[Any], Any]]


Model(x='math:cos')
```

## `dataclass_type`

This error is raised when the value is not valid for a `dataclass` field.

```py
from pydantic import ValidationError, dataclasses


@dataclasses.dataclass
class Nested:
    x: int


@dataclasses.dataclass
class Model:
    y: Nested


try:
    Model(y=1)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'dataclass_type'
```

Valid example:

```py
from pydantic import dataclasses


@dataclasses.dataclass
class Nested:
    x: int


@dataclasses.dataclass
class Model:
    y: Nested


Model(y=Nested(x=1))
```

## `date_from_datetime_inexact`

This error is raised when the `datetime` value provided for a `date` field
has a nonzero time component.
For a timestamp to parse into a field of type `date`, the time components
must all be zero.

```py
from datetime import date, datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


Model(x='2023-01-01')  # OK
Model(x=datetime(2023, 1, 1))  # OK

try:
    Model(x=datetime(2023, 1, 1, 12))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'date_from_datetime_inexact'
```

## `date_from_datetime_parsing`

This error is raised when the value is a string that is not valid for coercion to a `date`.

```py
from datetime import date

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


try:
    Model(x='XX1494012000')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'date_from_datetime_parsing'
```

## `date_future`

This error is raised when the value provided for a `FutureDate` field is not in the future.

```py
from datetime import date

from pydantic import BaseModel, FutureDate, ValidationError


class Model(BaseModel):
    x: FutureDate


try:
    Model(x=date(2000, 1, 1))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'date_future'
```

## `date_parsing`

This error is raised when the value for is not a valid JSON value for a `date` field.

```py
import json
from datetime import date

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: date = Field(strict=True)


try:
    Model.model_validate_json(json.dumps({'x': '1'}))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'date_parsing'
```

## `date_past`

This error is raised when the value provided for a `PastDate` field is not in the past.

```py
from datetime import date, timedelta

from pydantic import BaseModel, PastDate, ValidationError


class Model(BaseModel):
    x: PastDate


try:
    Model(x=date.today() + timedelta(1))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'date_past'
```

## `date_type`

This error is raised when the value type is not of type `date` for a strict `date` field.

```py
from datetime import date

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: date = Field(strict=True)


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'date_type'
```

## `datetime_aware`

This error is raised when the `datetime` value provided for a timezone-aware `datetime` field
doesn't have timezone information.

```py
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ValidationError


class Model(BaseModel):
    x: AwareDatetime


try:
    Model(x=datetime.now())
except ValidationError as exc_info:
    print(exc_info.errors())
    """
    [
        {
            'type': 'timezone_aware',
            'loc': ('x',),
            'msg': 'Input should have timezone info',
            'input': datetime.datetime(2032, 1, 2, 3, 4, 5, 6),
            'url': 'https://errors.pydantic.dev/2/v/timezone_aware',
        }
    ]
    """
```

## `datetime_future`

This error is raised when the value provided for a `FutureDatetime` field is not in the future.

```py
from datetime import datetime

from pydantic import BaseModel, FutureDatetime, ValidationError


class Model(BaseModel):
    x: FutureDatetime


try:
    Model(x=datetime(2000, 1, 1))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'datetime_future'
```

## `datetime_naive`

This error is raised when the `datetime` value provided for a timezone-naive `datetime` field
has timezone info.

```py
from datetime import datetime, timezone

from pydantic import BaseModel, NaiveDatetime, ValidationError


class Model(BaseModel):
    x: NaiveDatetime


try:
    Model(x=datetime.now(tz=timezone.utc))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'datetime_naive'
```

## `datetime_object_invalid`

This error is raised when something about the `datetime` object is not valid.

```py
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
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'datetime_object_invalid'
```

## `datetime_parsing`

This error is raised when the value provided for a `datetime` field can't be parsed as `datetime`.

```py
from datetime import datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: datetime


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'datetime_parsing'
```

## `datetime_past`

This error is raised when the value provided for a `PastDatetime` field is not in the past.

```py
from datetime import datetime, timedelta

from pydantic import BaseModel, PastDatetime, ValidationError


class Model(BaseModel):
    x: PastDatetime


try:
    Model(x=datetime.now() + timedelta(100))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'datetime_past'
```

## `datetime_type`

This error is raised when the value type is not `datetime` for a strict `datetime` field.

```py
from datetime import date, datetime

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: datetime = Field(strict=True)


try:
    Model(x=date(2023, 1, 1))
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'datetime_type'
```

## `dict_attributes_type`

This error is raised when the input is not a valid dictionary or instance to extract fields from.

```py
from typing import Union

from typing_extensions import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


class Cat(BaseModel):
    pet_type: Literal['cat']
    m: str


class Model(BaseModel):
    pet: Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]
    number: int


try:
    Model.model_validate({'pet': 'fish', 'number': 2})
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'dict_attributes_type'
```

Valid example:

```py
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model.model_validate({'x': 'test'})
```

## `dict_type`

This error is raised when the value type is not `dict` for a `dict` field.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict


try:
    Model(x=['1', '2'])
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'dict_type'
```

## `extra_forbidden`

This error is raised when the input values contain extra fields and `model_config['extra'] == 'forbid'`.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: str

    model_config = ConfigDict(extra='forbid')


try:
    Model(x='test', y='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'extra_forbidden'
```

You can read more about the `extra` configuration on the [Extra Attributes](model_config.md#extra-attributes) section.

## `finite_number`

This error is raised when the value is an infinite number.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=2.2250738585072011e308)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'finite_number'
```

## `float_parsing`

This error is raised when the value can't be parsed as `float`.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: float


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'float_parsing'
```

## `float_type`

This error is raised when the value type is not `float`.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: float


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'float_type'
```

## `frozen_field`

This error is raised when the `config.validate_assignment=True` and you assign
a value to a field with `Field.frozen=True`.

```py
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Model(BaseModel):
    x: str = Field('test', frozen=True)

    model_config = ConfigDict(validate_assignment=True)


model = Model()
try:
    model.x = 'test1'
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'frozen_field'
```

## `frozen_instance`

This error is raised when the model is frozen and you assign a new value to
one of the fields.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(frozen=True)


m = Model(x=1)
try:
    m.x = 2
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'frozen_instance'
```

## `frozen_set_type`

This error is raised when the value type is not `frozenset`.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: frozenset


try:
    model = Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'frozen_set_type'
```

## `get_attribute_error`

This error is raised when `config.from_attributes=True` and an error occurs during collecting values.

```py
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
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'get_attribute_error'
```

## `greater_than`

This error is raised when the value is not greater than `Field.gt`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(gt=10)


try:
    Model(x=10)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'greater_than'
```

## `greater_than_equal`

This error is raised when the value is not greater than or equal to the specified constraint.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(ge=10)


try:
    Model(x=9)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'greater_than_equal'
```

## `int_from_float`

This error is raised when you provide a `float` value for an `int` field.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=0.5)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'int_from_float'
```

## `int_parsing`

This error is raised when the value can't be parsed as `int`.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'int_parsing'
```

## `int_type`

This error is raised when the value type is not `int`.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'int_type'
```

## `invalid_key`

This error is raised when the type of a `dict` key is not valid.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')


try:
    Model.model_validate({'x': 1, b'y': 2})
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'invalid_key'
```

## `is_instance_of`

This error is raised when the input value is not an instance of the expected type.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Nested:
    x: str


class Model(BaseModel):
    y: Nested

    model_config = ConfigDict(arbitrary_types_allowed=True)


try:
    Model(y='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'is_instance_of'
```

## `is_subclass_of`

This error is raised when the input value is not a subclass of expected type.

```py
from typing import Type

from pydantic import BaseModel, ValidationError


class Nested:
    x: str


class Model(BaseModel):
    y: Type[Nested]


try:
    Model(y='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'is_subclass_of'
```

## `iterable_type`

This error is raised when the input value is not an `Iterable`.

```py
from typing import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    y: Iterable


try:
    Model(y=123)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'iterable_type'
```

## `iteration_error`

This error is raised when an error occurs during iteration.

```py
from typing import List

from pydantic import BaseModel, ValidationError


def gen():
    yield 1
    raise RuntimeError('error')


class Model(BaseModel):
    x: List[int]


try:
    Model(x=gen())
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'iteration_error'
```

## `json_invalid`

This error is raised when the input value is not a valid JSON string.

```py
from pydantic import BaseModel, Json, ValidationError


class Model(BaseModel):
    x: Json


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'json_invalid'
```

## `json_type`

This error is raised when the input value is of a type that cannot be parsed as JSON.

```py
from pydantic import BaseModel, Json, ValidationError


class Model(BaseModel):
    x: Json


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'json_type'
```

## `less_than`

This error is raised when the value is not less than `Field.lt`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(lt=10)


try:
    Model(x=10)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'less_than'
```

## `less_than_equal`

This error is raised when the value is not less than or equal to the specified constraint.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(le=10)


try:
    Model(x=11)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'less_than_equal'
```

## `list_type`

This error is raised when the input value is not a `list`.

```py
from typing import List

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: List[int]


try:
    Model(x=1)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'list_type'
```

## `literal_error`

This error is raised when the input value is not in expected literals.

```py
from typing_extensions import Literal

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Literal['a']


try:
    Model(x='b')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'literal_error'
```

## `mapping_type`

This error is raised when the input value is not a valid mapping.

```py
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
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'mapping_type'
```

## `missing`

This error is raised when you don't provide required input fields.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model()
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'missing'
```

## `missing_argument`

This error is raised when you missed arguments in calling a function
decorated by `validate_call`.

```py
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int):
    return a


try:
    foo()
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'missing_argument'
```

## `missing_keyword_only_argument`

This error is raised when you missed keyword-only arguments in calling
a function decorated by `validate_call`.

```py
from pydantic import ValidationError, validate_call


@validate_call
def foo(*, a: int):
    return a


try:
    foo()
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'missing_keyword_only_argument'
```

## `missing_positional_only_argument`

This error is raised when you missed positional-only arguments in calling
a function decorated by `validate_call`.

```py requires="3.8"
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int, /):
    return a


try:
    foo()
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'missing_positional_only_argument'
```

## `model_class_type`

This error is raised when you validate with `strict=True` and
the input value is not an instance of the model.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model.model_validate({'x': 'test'}, strict=True)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'model_class_type'
```

Valid example:

```py
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model.model_validate(Model(x='test'), strict=True)
```

## `multiple_argument_values`

This error is raised when you provide multiple values for an argument
in calling a function decorated by `validate_call`.

```py
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int):
    return a


try:
    foo(1, a=2)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'multiple_argument_values'
```

## `multiple_of`

This error is raised when the input is not a multiple of `FieldInfo.multiple_of`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(multiple_of=5)


try:
    Model(x=1)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'multiple_of'
```

## `no_such_attribute`

This error is raised when you assign a value to an attribute that does not exist.

```py
from pydantic import ConfigDict, ValidationError, dataclasses


@dataclasses.dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass:
    x: int


m = MyDataclass(x=1)
try:
    m.y = 10
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'no_such_attribute'
```

## `none_required`

This error is raised when the input value is not `None` for a field that
requires `None`.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: None


try:
    Model(x=1)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'none_required'
```

## `recursion_loop`

This error is raised when a cyclic reference is detected.

```py
from typing import List

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: List['Model']


d = {'x': []}
d['x'].append(d)
try:
    Model(**d)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'recursion_loop'
```

## `set_type`

This error is raised when the value type is not `set`.

```py
from typing import Set

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Set[int]


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'set_type'
```

## `string_pattern_mismatch`

This error is raised when the value doesn't match with `Field.pattern`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(pattern='test')


try:
    Model(x='1')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'string_pattern_mismatch'
```

## `string_sub_type`

This error is raised when the value is not an instance of a
subclass of string when `Field.strict=True`.

```py
from enum import Enum

from pydantic import BaseModel, Field, ValidationError


class MyEnum(str, Enum):
    foo = 'foo'


class Model(BaseModel):
    x: str = Field(strict=True)


try:
    Model(x=MyEnum.foo)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'string_sub_type'
```

## `string_too_long`

This error is raised when the string value length is greater than `Field.max_length`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(max_length=3)


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'string_too_long'
```

## `string_too_short`

This error is raised when the string value length is less than `Field.min_length`.

```py
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(min_length=3)


try:
    Model(x='t')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'string_too_short'
```

## `string_type`

This error is raised when the value is not a string.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model(x=1)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'string_type'
```

## `string_unicode`

This error is raised when the value cannot be parsed as a Unicode string.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model(x=b'\x81')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'string_unicode'
```

## `time_delta_parsing`

This error is raised when the value provided for a `timedelta` field cannot be parsed.

```py
from datetime import timedelta

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: timedelta


try:
    Model(x='t')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'time_delta_parsing'
```

## `time_delta_type`

This error is raised when the value type is not valid for a `timedelta` field.

```py
from datetime import timedelta

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: timedelta


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'time_delta_type'
```

## `time_parsing`

This error is raised when the value provided for a `time` field cannot be parsed.

```py
from datetime import time

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: time


try:
    Model(x='25:20:30.400')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'time_parsing'
```

## `time_type`

This error is raised when the value type is not valid for a `time` field.

```py
from datetime import time

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: time


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'time_type'
```

## `too_long`

This error is raised when the value length is greater than `Field.max_length`.

```py
from typing import List

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: List[int] = Field(max_length=3)


try:
    Model(x=[1, 2, 3, 4])
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'too_long'
```

## `too_short`

This error is raised when the value length is less than `Field.min_length`.

```py
from typing import List

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: List[int] = Field(min_length=3)


try:
    Model(x=[1, 2])
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'too_short'
```

## `tuple_type`

This error is raised when the value type is not valid for a `tuple` field.

```py
from typing import Tuple

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Tuple[int]


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'tuple_type'
```

## `unexpected_keyword_argument`

This error is raised when you provide a value by keyword for a positional-only
argument in calling a function decorated by `validate_call`.

```py requires="3.8"
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int, /):
    return a


try:
    foo(a=2)
except ValidationError as exc_info:
    assert exc_info.errors()[1]['type'] == 'unexpected_keyword_argument'
```

## `unexpected_positional_argument`

This error is raised when you provide a positional value for a keyword-only
argument in calling a function decorated by `validate_call`.

```py
from pydantic import ValidationError, validate_call


@validate_call
def foo(*, a: int):
    return a


try:
    foo(2)
except ValidationError as exc_info:
    assert exc_info.errors()[1]['type'] == 'unexpected_positional_argument'
```

## `union_tag_invalid`

This error is raised when the tag does not match any of the expected tags.

```py
from typing import Union

from typing_extensions import Literal

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(..., discriminator='pet_type')


try:
    Model(cat={'pet_type': 't'})
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'union_tag_invalid'
```

## `union_tag_not_found`

This error is raised when it is not possible to extract a tag using the discriminator.

```py
from typing import Union

from typing_extensions import Literal

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(..., discriminator='pet_type')


try:
    Model(cat={'name': 'blackcat'})
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'union_tag_not_found'
```

## `url_parsing`

This error is raised when the input value cannot be parsed as a URL.

```py
from pydantic import AnyUrl, BaseModel, ValidationError


class Model(BaseModel):
    x: AnyUrl


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'url_parsing'
```

## `url_scheme`

This error is raised when the URL scheme is not valid for the URL type of the field.

```py
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x='ftp://example.com')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'url_scheme'
```

## `url_syntax_violation`

This error is raised when the URL syntax is not valid.

```py
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl = Field(strict=True)


try:
    Model(x='http:////example.com')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'url_syntax_violation'
```

## `url_too_long`

This error is raised when the URL length is greater than 2083.

```py
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x='x' * 2084)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'url_too_long'
```

## `url_type`

This error is raised when the input value type is not valid for a URL field.

```py
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x=None)
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'url_type'
```

## `value_error`

This error is raised when there is a `ValueError` during validation.

```py
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    x: str

    @field_validator('x')
    @classmethod
    def repeat_b(cls, v):
        raise ValueError()


try:
    Model(x='test')
except ValidationError as exc_info:
    assert exc_info.errors()[0]['type'] == 'value_error'
```
