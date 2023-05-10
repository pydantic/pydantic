Below are details on common validation errors users may encounter when working with pydantic, together
with some suggestions on how to fix them.

## `arguments_type`

This error is raised when arguments passed to a function are not
a tuple, list or a dictionary.

## `assertion_error`

This error is raised when there is a failing assertion during the validation.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    @classmethod
    def force_x_positive(cls, v):
        assert v > 0
        return v

Model(x=-1)
```

## `bool`


## `bool_parsing`

This error is raised when the value is an invalid boolean string.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: bool

print(Model(x='test'))
```

## `bool_type`

This error is raised when the value type is not valid for a boolean field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: bool

Model(x=None)
```

## `bytes_too_long`

This error is raised when the bytes value length is greater than `Field.max_length`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: bytes = Field(max_length=3)

Model(x=b'test')
```

## `bytes_too_short`

This error is raised when the bytes value length is less than `Field.min_length`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: bytes = Field(min_length=3)

Model(x=b't')
```

## `bytes_type`

This error is raised when the value type is not valid for a bytes field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: bytes

Model(x=123)
```

## `callable_type`

This error is raised when the value is not a `callable`.

```py test="skip" lint="skip" upgrade="skip"
from typing import Any, Callable

from pydantic import BaseModel, ImportString


class Model(BaseModel):
    x: ImportString[Callable[[Any], Any]]


Model(x='os.path')
```

Valid example:

```py test="skip" lint="skip" upgrade="skip"
from typing import Any, Callable

from pydantic import BaseModel, ImportString


class Model(BaseModel):
    x: ImportString[Callable[[Any], Any]]


Model(x='math.cos')
```

## `dataclass_type`

This error is raised when the value is not valid for a dataclass field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import dataclasses


@dataclasses.dataclass
class Nested:
    x: int


@dataclasses.dataclass
class Model:
    y: Nested


Model(y=1)
```

Valid example:

```py test="skip" lint="skip" upgrade="skip"
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

This error is raised when the datetime value provided for a date field is not an exact date.

```py test="skip" lint="skip" upgrade="skip"
from datetime import date, datetime

from pydantic import BaseModel


class Model(BaseModel):
    x: date


Model(x=datetime(2023, 1, 1, 12))
```

## `date_from_datetime_parsing`

This error is raised when the datetime value provided for a date field is invalid.

```py test="skip" lint="skip" upgrade="skip"
from datetime import date

from pydantic import BaseModel


class Model(BaseModel):
    x: date


Model(x='XX1494012000')
```

## `date_future`

This error is raised when the value provided for a `FutureDate` field is not in the future.

```py test="skip" lint="skip" upgrade="skip"
from datetime import date

from pydantic import BaseModel, FutureDate


class Model(BaseModel):
    x: FutureDate


Model(x=date(2000, 1, 1))
```

## `date_parsing`

This error is raised when the value for is not a valid json value for a date field.

```py test="skip" lint="skip" upgrade="skip"
import json
from datetime import date

from pydantic import BaseModel, Field


class Model(BaseModel):
    x: date = Field(strict=True)


Model.model_validate_json(json.dumps({'x': '1'}))
```

## `date_past`

This error is raised when the value provided for a `PastDate` field is not in the past.

```py test="skip" lint="skip" upgrade="skip"
from datetime import date, timedelta

from pydantic import BaseModel, PastDate


class Model(BaseModel):
    x: PastDate


Model(x=date.today() + timedelta(1))
```


## `date_type`

This error is raised when the value type is not date for a strict date field.

```py test="skip" lint="skip" upgrade="skip"
from datetime import date

from pydantic import BaseModel, Field


class Model(BaseModel):
    x: date = Field(strict=True)


Model(x='test')
```

## `datetime_aware`

This error is raised when the datetime value provided for a timezone aware datetime field
doesn't have timezone info.

```py test="skip" lint="skip" upgrade="skip"
from datetime import datetime

from pydantic import BaseModel, AwareDatetime


class Model(BaseModel):
    x: AwareDatetime


Model(x=datetime.now())
```

## `datetime_future`

This error is raised when the value provided for a `FutureDatetime` field is not in the future.

```py test="skip" lint="skip" upgrade="skip"
from datetime import datetime

from pydantic import BaseModel, FutureDatetime


class Model(BaseModel):
    x: FutureDatetime


Model(x=datetime(2000, 1, 1))
```

## `datetime_naive`

This error is raised when the datetime value provided for a timezone naive datetime field
has timezone info.

```py test="skip" lint="skip" upgrade="skip"
from datetime import datetime, timezone

from pydantic import BaseModel, NaiveDatetime


class Model(BaseModel):
    x: NaiveDatetime


Model(x=datetime.now(tz=timezone.utc))
```

## `datetime_object_invalid`

This error is raised when the datetime object is invalid.

```py test="skip" lint="skip" upgrade="skip"
from datetime import datetime, tzinfo

from pydantic import BaseModel, AwareDatetime

class CustomTz(tzinfo):
    # utcoffset is not implemented!

    def tzname(self, _dt):
        return 'CustomTZ'


class Model(BaseModel):
    x: AwareDatetime


Model(x=datetime(2023, 1, 1, tzinfo=CustomTz()))
```

## `datetime_parsing`

This error is raised when the value provided for a datetime field can't be parsed as datetime.

```py test="skip" lint="skip" upgrade="skip"
from datetime import datetime

from pydantic import BaseModel


class Model(BaseModel):
    x: datetime


Model(x='test')
```

## `datetime_past`

This error is raised when the value provided for a `PastDatetime` field is not in the past.

```py test="skip" lint="skip" upgrade="skip"
from datetime import datetime, timedelta

from pydantic import BaseModel, PastDatetime


class Model(BaseModel):
    x: PastDatetime


odel(x=datetime.now() + timedelta(100))
```

## `datetime_type`

This error is raised when the value type is not datetime for a strict datetime field.

```py test="skip" lint="skip" upgrade="skip"
from datetime import date, datetime

from pydantic import BaseModel, Field


class Model(BaseModel):
    x: datetime = Field(strict=True)


Model(x=date(2023, 1, 1))
```

## `dict_attributes_type`

This error is raised when the input is not a valid dict or instanec to extract fields from.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model.model_validate('test')
```

Valid example:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model.model_validate({'x': 'test'})
```

## `dict_type`

This error is raised when the value type is not dict for dict field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: dict


Model(x=['1', '2'])
```

## `extra_forbidden`

This error is raised when the input values contain extra field and `config.extra=forbid`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    x: str

    model_config = ConfigDict(extra='forbid')


Model(x='test', y='test')
```

## `finite_number`

This error is raised when the value is an infinite number.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: int


Model(x=2.2250738585072011e308)
```

## `float_parsing`

This error is raised when the value can't be parsed as float.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: float


Model(x='test')
```

## `float_type`

This error is raised when the value type is not float.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: float


Model(x=None)
```

## `frozen_field`


This error is raised when the `config.validate_assignment=True` and you assign
a value to a field with `Field.frozen=True`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    x: str = Field('test', frozen=True)

    model_config = ConfigDict(validate_assignment=True)


model = Model()
model.x = 'test1'
```

## `frozen_instance`

This error is raised when the model is frozen and you assign a new value to
one of the fields.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    x: int

    model_config = ConfigDict(frozen=True)

m = Model(x=1)
m.x = 2
```

## `frozen_set_type`

This error is raised when the value type is not frozenset.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: frozenset


model = Model(x='test')
```

## `get_attribute_error`

This error is raised when `config.from_attributes=True` and an error occurs during collecting values.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


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


Model.model_validate(Foobar())
```

## `greater_than`

This error is raised when the value is not greater than `Field.gt`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: int = Field(gt=10)


Model(x=10)
```

## `greater_than_equal`

This error is raised when the value is not greater than equal `Field.ge`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: int = Field(ge=10)


Model(x=9)
```

## `int_from_float`

This error is raised when you provide a float value for an int field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: int


Model(x=0.5)
```

## `int_parsing`

This error is raised when the value can't be parsed as int.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: int


Model(x='test')
```

## `int_type`

This error is raised when the value type is not int.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: int


Model(x=None)
```

## `invalid_key`

This error is raised when the key type is invalid.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')
```

Model.model_validate({'x': 1, b'y': 2})

## `is_instance_of`

This error is raised when the input value is not an instance of expected type.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


class Nested:
    x: str


class Model(BaseModel):
    y: Nested

    model_config = ConfigDict(arbitrary_types_allowed=True)


Model(y='test')
```

## `is_subclass_of`

This error is raised when the input value is not a sub-class of expected type.

```py test="skip" lint="skip" upgrade="skip"
from typing import Type

from pydantic import BaseModel


class Nested:
    x: str


class Model(BaseModel):
    y: Type[Nested]


Model(y='test')
```

## `iterable_type`

This error is raised when the input value is not an `Iterable`.

```py test="skip" lint="skip" upgrade="skip"
from typing import Iterable

from pydantic import BaseModel


class Model(BaseModel):
    y: Iterable


Model(y=123)
```

## `iteration_error`

This error is raised when an error occurs during iteration.

```py test="skip" lint="skip" upgrade="skip"
from typing import List

from pydantic import BaseModel


def gen():
    yield 1
    raise RuntimeError('error')


class Model(BaseModel):
    x: List[int]


Model(x=gen())
```

## `json_invalid`

This error is raised when the input value is an invalid json string.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Json


class Model(BaseModel):
    x: Json


Model(x='test')
```

## `json_type`

This error is raised when the input value type is not json string.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Json


class Model(BaseModel):
    x: Json


Model(x=None)
```

## `less_than`

This error is raised when the value is not less than `Field.lt`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: int = Field(lt=10)


Model(x=10)
```

## `less_than_equal`

This error is raised when the value is not less than equal `Field.le`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: int = Field(le=10)


Model(x=11)
```

## `list_type`

This error is raised when the input value is not a list.

```py test="skip" lint="skip" upgrade="skip"
from typing import List

from pydantic import BaseModel


class Model(BaseModel):
    x: List[int]


Model(x=1)
```

## `literal_error`

This error is raised when the input value is not in expected literals.

```py test="skip" lint="skip" upgrade="skip"
from typing_extensions import Literal

from pydantic import BaseModel


class Model(BaseModel):
    x: Literal['a']


Model(x='b')
```

## `mapping_type`

This error is raised when the input value is not a valid mapping.

```py test="skip" lint="skip" upgrade="skip"
from collections.abc import Mapping
from typing import Dict

from pydantic import BaseModel


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


Model(x=BadMapping())
```

## `missing`

This error is raised when you don't provide required input fields.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model()
```

## `missing_argument`

This error is raised when you missed arguments in calling a function
decorated by `validate_call`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import validate_call


@validate_call
def foo(a: int):
    return a


foo()
```

## `missing_keyword_only_argument`

This error is raised when you missed keyword-only arguments in calling
a function decorated by `validate_call`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import validate_call


@validate_call
def foo(*, a: int):
    return a


foo()
```

## `missing_positional_only_argument`

This error is raised when you missed positional-only arguments in calling
a function decorated by `validate_call`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import validate_call


@validate_call
def foo(a: int, /):
    return a


foo()
```

## `model_class_type`

This error is raised when you validate with `strict=True` and
input value is not an instance of model.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model.model_validate({'x': 'test'}, strict=True)
```

Valid example:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model.model_validate(Model(x='test'), strict=True)
```

## `multiple_argument_values`

This error is raised when you provide multiple values for an argument
in calling a function decorated by `validate_call`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import validate_call


@validate_call
def foo(a: int):
    return a


foo(1, a=2)
```

## `multiple_of`

This error is raised when the input is not multiple of `Field.multiple_of`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: int = Field(multiple_of=5)


Model(x=1)
```

## `no_such_attribute`

This error is raised when you assign value to a non-existing attribute.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import ConfigDict, dataclasses


@dataclasses.dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass:
    x: int


m = MyDataclass(x=1)
m.y = 10
```

## `none_required`

This error is raised when the input value is not `None` for a field that
requires `None`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: None


Model(x=1)
```

## `recursion_loop`

This error is raised when cyclic reference detected.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: list['Model']

d = {'x': []}
d['x'].append(d)
Model(**d)
```

## `set_type`

This error is raised when the value type is not set.

```py test="skip" lint="skip" upgrade="skip"
from typing import Set

from pydantic import BaseModel


class Model(BaseModel):
    x: Set[int]


Model(x='test')
```

## `string_pattern_mismatch`

This error is raised when the value doesn't match with `Field.pattern`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: str = Field(pattern='test')


Model(x='1')
```

## `string_sub_type`

This error is raised when the value is not an instance of a
subclass of string when `Field.strict=True`.

```py test="skip" lint="skip" upgrade="skip"
from enum import Enum

from pydantic import BaseModel, Field


class MyEnum(str, Enum):
    foo = 'foo'


class Model(BaseModel):
    x: str = Field(strict=True)


Model(x=MyEnum.foo)
```

## `string_too_long`

This error is raised when the string value length is greater than `Field.max_length`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: str = Field(max_length=3)


Model(x='test')
```

## `string_too_short`

This error is raised when the string value length is less than `Field.min_length`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: str = Field(min_length=3)


Model(x='t')
```

## `string_type`

This error is raised when the value type is not string.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str


Model(x=1)
```

## `string_unicode`

This error is raised when the value cannot be parsed as unicode string.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: str

Model(x=b'\x81')
```

## `time_delta_parsing`

This error is raised when the value provided for a timedelta field cannot be parsed.

```py test="skip" lint="skip" upgrade="skip"
from datetime import timedelta

from pydantic import BaseModel


class Model(BaseModel):
    x: timedelta


Model(x='t')
```

## `time_delta_type`

This error is raised when the value type is not valid for a timedelta field.

```py test="skip" lint="skip" upgrade="skip"
from datetime import timedelta

from pydantic import BaseModel


class Model(BaseModel):
    x: timedelta


Model(x=None)
```

## `time_parsing`

This error is raised when the value provided for a time field cannot be parsed.

```py test="skip" lint="skip" upgrade="skip"
from datetime import time

from pydantic import BaseModel


class Model(BaseModel):
    x: time


Model(x='25:20:30.400')
```

## `time_type`

This error is raised when the value type is not valid for a time field.

```py test="skip" lint="skip" upgrade="skip"
from datetime import time

from pydantic import BaseModel


class Model(BaseModel):
    x: time


Model(x=None)
```

## `too_long`

This error is raised when the value length is greater than `Field.max_length`.

```py test="skip" lint="skip" upgrade="skip"
from typing import List

from pydantic import BaseModel, Field


class Model(BaseModel):
    x: List[int] = Field(max_length=3)


Model(x=[1, 2, 3, 4])
```

## `too_short`

This error is raised when the value length is less than `Field.min_length`.

```py test="skip" lint="skip" upgrade="skip"
from typing import List

from pydantic import BaseModel, Field


class Model(BaseModel):
    x: List[int] = Field(min_length=3)


Model(x=[1, 2])
```

## `tuple_type`

This error is raised when the value type is not valid for a tuple field.

```py test="skip" lint="skip" upgrade="skip"
from typing import Tuple

from pydantic import BaseModel


class Model(BaseModel):
    x: Tuple[int]


Model(x=None)
```

## `unexpected_keyword_argument`

This error is raised when you provide a value by keyword for a positional-only
argument in calling a function decorated by `validate_call`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import validate_call


@validate_call
def foo(a: int, /):
    return a


foo(a=2)
```

## `unexpected_positional_argument`

This error is raised when you provide a positional value for a keyword-only
argument in calling a function decorated by `validate_call`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import validate_call


@validate_call
def foo(*, a: int):
    return a


foo(2)
```

## `union_tag_invalid`

This error is raised when the tag does not match any of the expected tags.

```py test="skip" lint="skip" upgrade="skip"
from typing import Union
from typing_extensions import Literal

from pydantic import BaseModel, Field


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(..., discriminator='pet_type')

Model(cat={'pet_type': 't'})
```

## `union_tag_not_found`

This error is raised when it is not possible to extract tag using discriminator.

```py test="skip" lint="skip" upgrade="skip"
from typing import Union
from typing_extensions import Literal

from pydantic import BaseModel, Field


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(..., discriminator='pet_type')

Model(cat={'name': 'blackcat'})
```

## `url_parsing`

This error is raised when the input value cannot be parsed as a url.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, AnyUrl


class Model(BaseModel):
    x: AnyUrl


Model(x='test')
```

## `url_scheme`

This error is raised when the url schema is not valid for the url type.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, HttpUrl


class Model(BaseModel):
    x: HttpUrl


Model(x='ftp://example.com')
```

## `url_syntax_violation`

This error is raised when the url syntax is invalid.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field, HttpUrl


class Model(BaseModel):
    x: HttpUrl = Field(strict=True)


Model(x='http:////example.com')
```

## `url_too_long`

This error is raised when the url length is greater than 2083.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, HttpUrl


class Model(BaseModel):
    x: HttpUrl


Model(x='x' * 2084)
```

## `url_type`

This error is raised when the input value type is not valid for a url field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, HttpUrl


class Model(BaseModel):
    x: HttpUrl


Model(x='x' * 2084)
```

## `value_error`

This error is raised when there is a `ValueError` during validation.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    x: str

    @field_validator('x')
    @classmethod
    def repeat_b(cls, v):
        raise ValueError()


Model(x='test')
```
