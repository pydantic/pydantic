Custom validation and complex relationships between objects can be achieved using the `validator` decorator.

```py
from pydantic_core.core_schema import FieldValidationInfo

from pydantic import BaseModel, ValidationError, field_validator


class UserModel(BaseModel):
    name: str
    username: str
    password1: str
    password2: str

    @field_validator('name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

    @field_validator('password2')
    def passwords_match(cls, v, info: FieldValidationInfo):
        if 'password1' in info.data and v != info.data['password1']:
            raise ValueError('passwords do not match')
        return v

    @field_validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v


user = UserModel(
    name='samuel colvin',
    username='scolvin',
    password1='zxcvbn',
    password2='zxcvbn',
)
print(user)
#> name='Samuel Colvin' username='scolvin' password1='zxcvbn' password2='zxcvbn'

try:
    UserModel(
        name='samuel',
        username='scolvin',
        password1='zxcvbn',
        password2='zxcvbn2',
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for UserModel
    name
      Value error, must contain a space [type=value_error, input_value='samuel', input_type=str]
    password2
      Value error, passwords do not match [type=value_error, input_value='zxcvbn2', input_type=str]
    """
```

A few things to note on validators:

* validators are "class methods", so the first argument value they receive is the `UserModel` class, not an instance
  of `UserModel`.
* the second argument is always the field value to validate; it can be named as you please
* you can also add any subset of the following arguments to the signature (the names **must** match):
  * `values`: a dict containing the name-to-value mapping of any previously-validated fields
  * `config`: the model config
  * `field`: the field being validated. Type of object is `pydantic.fields.ModelField`.
  * `**kwargs`: if provided, this will include the arguments above not explicitly listed in the signature
* validators should either return the parsed value or raise a `ValueError`, `TypeError`, or `AssertionError`
  (``assert`` statements may be used).

!!! warning
    If you make use of `assert` statements, keep in mind that running
    Python with the [`-O` optimization flag](https://docs.python.org/3/using/cmdline.html#cmdoption-o)
    disables `assert` statements, and **validators will stop working**.

* where validators rely on other values, you should be aware that:

  * Validation is done in the order fields are defined.
    E.g. in the example above, `password2` has access to `password1` (and `name`),
    but `password1` does not have access to `password2`. See [Field Ordering](models.md#field-ordering)
    for more information on how fields are ordered

  * If validation fails on another field (or that field is missing) it will not be included in `values`, hence
    `if 'password1' in values and ...` in this example.

## Pre and per-item validators

Validators can do a few more complex things:

```py
from typing import List

from typing_extensions import Annotated

from pydantic import BaseModel, ValidationError, field_validator
from pydantic.validators import AfterValidator


def check_squares(v: int) -> int:
    assert v**0.5 % 1 == 0, f'{v} is not a square number'
    return v


def check_cubes(v: int) -> int:
    # 64 ** (1 / 3) == 3.9999999999999996 (!)
    # this is not a good way of checking cubes
    assert v ** (1 / 3) % 1 == 0, f'{v} is not a cubed number'
    return v


SquaredNumber = Annotated[int, AfterValidator(check_squares)]
CubedNumberNumber = Annotated[int, AfterValidator(check_cubes)]


class DemoModel(BaseModel):
    square_numbers: List[SquaredNumber] = []
    cube_numbers: List[CubedNumberNumber] = []

    @field_validator('square_numbers', 'cube_numbers', mode='before')
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split('|')
        return v

    @field_validator('cube_numbers', 'square_numbers')
    def check_sum(cls, v):
        if sum(v) > 42:
            raise ValueError('sum of numbers greater than 42')
        return v


print(DemoModel(square_numbers=[1, 4, 9]))
#> square_numbers=[1, 4, 9] cube_numbers=[]
print(DemoModel(square_numbers='1|4|16'))
#> square_numbers=[1, 4, 16] cube_numbers=[]
print(DemoModel(square_numbers=[16], cube_numbers=[8, 27]))
#> square_numbers=[16] cube_numbers=[8, 27]
try:
    DemoModel(square_numbers=[1, 4, 2])
except ValidationError as e:
    print(e)
    """
    1 validation error for DemoModel
    square_numbers.2
      Assertion failed, 2 is not a square number
    assert ((2 ** 0.5) % 1) == 0 [type=assertion_error, input_value=2, input_type=int]
    """

try:
    DemoModel(cube_numbers=[27, 27])
except ValidationError as e:
    print(e)
    """
    1 validation error for DemoModel
    cube_numbers
      Value error, sum of numbers greater than 42 [type=value_error, input_value=[27, 27], input_type=list]
    """
```

A few more things to note:

* a single validator can be applied to multiple fields by passing it multiple field names
* a single validator can also be called on *all* fields by passing the special value `'*'`
* the keyword argument `mode='before'` will cause the validator to be called prior to other validation
* using validator annotations inside of Annotated allows applying validators to items of collections

### Generic validated collections

To validate individual items of a collection (list, dict, etc.) field you can use `Annotated` to apply validators to the inner items.
In this example we also use type aliases to create a generic validated collection to demonstrate how this approach leads to composability and coda re-use.

```py
from typing import List, TypeVar

from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.validators import AfterValidator

T = TypeVar('T')

SortedList = Annotated[List[T], AfterValidator(lambda x: sorted(x))]

Name = Annotated[str, AfterValidator(lambda x: x.title())]


class DemoModel(BaseModel):
    int_list: SortedList[int]
    name_list: SortedList[Name]


print(DemoModel(int_list=[3, 2, 1], name_list=['adrian g', 'David']))
#> int_list=[1, 2, 3] name_list=['Adrian G', 'David']
```

## Validate Always

For performance reasons, by default validators are not called for fields when a value is not supplied.
However there are situations where it may be useful or required to always call the validator, e.g.
to set a dynamic default value.

```py test="xfail - we need default value validation"
from datetime import datetime

from pydantic import BaseModel, validator


class DemoModel(BaseModel):
    ts: datetime = None

    @validator('ts', pre=True, always=True)
    def set_ts_now(cls, v):
        return v or datetime.now()


print(DemoModel())
print(DemoModel(ts='2017-11-08T14:00'))
```

You'll often want to use this together with `pre`, since otherwise with `always=True`
*pydantic* would try to validate the default `None` which would cause an error.

## Reuse validators

Occasionally, you will want to use the same validator on multiple fields/models (e.g. to
normalize some input data). The "naive" approach would be to write a separate function,
then call it from multiple decorators.  Obviously, this entails a lot of repetition and
boiler plate code. To circumvent this, the `allow_reuse` parameter has been added to
`pydantic.validator` in **v1.2** (`False` by default):

```py
from pydantic import BaseModel, field_validator


def normalize(name: str) -> str:
    return ' '.join((word.capitalize()) for word in name.split(' '))


class Producer(BaseModel):
    name: str

    # validators
    normalize_name = field_validator('name')(normalize)


class Consumer(BaseModel):
    name: str

    # validators
    normalize_name = field_validator('name')(normalize)


jane_doe = Producer(name='JaNe DOE')
john_doe = Consumer(name='joHN dOe')
assert jane_doe.name == 'Jane Doe'
assert john_doe.name == 'John Doe'
```

As it is obvious, repetition has been reduced and the models become again almost
declarative.

!!! tip
    If you have a lot of fields that you want to validate, it usually makes sense to
    define a help function with which you will avoid setting `allow_reuse=True` over and
    over again.

## Model Validators

Validation can also be performed on the entire model's data.

```py
from pydantic import BaseModel, ValidationError, model_validator


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str

    @model_validator(mode='before')
    def check_card_number_omitted(cls, data):
        assert 'card_number' not in data, 'card_number should not be included'
        return data

    @model_validator(mode='after')
    def check_passwords_match(cls, m: 'UserModel'):
        pw1 = m.password1
        pw2 = m.password2
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        return m


print(UserModel(username='scolvin', password1='zxcvbn', password2='zxcvbn'))
#> username='scolvin' password1='zxcvbn' password2='zxcvbn'
try:
    UserModel(username='scolvin', password1='zxcvbn', password2='zxcvbn2')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
      Value error, passwords do not match [type=value_error, input_value={'username': 'scolvin', '... 'password2': 'zxcvbn2'}, input_type=dict]
    """

try:
    UserModel(
        username='scolvin',
        password1='zxcvbn',
        password2='zxcvbn',
        card_number='1234',
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
      Assertion failed, card_number should not be included
    assert 'card_number' not in {'card_number': '1234', 'password1': 'zxcvbn', 'password2': 'zxcvbn', 'username': 'scolvin'} [type=assertion_error, input_value={'username': 'scolvin', '..., 'card_number': '1234'}, input_type=dict]
    """
```

As with field validators, root validators can have `pre=True`, in which case they're called before field
validation occurs (and are provided with the raw input data), or `pre=False` (the default), in which case
they're called after field validation.

Field validation will not occur if `pre=True` root validators raise an error. As with field validators,
"post" (i.e. `pre=False`) root validators by default will be called even if prior validators fail; this
behaviour can be changed by setting the `skip_on_failure=True` keyword argument to the validator.
The `values` argument will be a dict containing the values which passed field validation and
field defaults where applicable.

## Field Checks

On class creation, validators are checked to confirm that the fields they specify actually exist on the model.

Occasionally however this is undesirable: e.g. if you define a validator to validate fields on inheriting models.
In this case you should set `check_fields=False` on the validator.

## Dataclass Validators

Validators also work with *pydantic* dataclasses.

**TODO: Change this example so that it *should* use a validator; right now it would be better off with default_factory..**

```py
from datetime import datetime

from pydantic import Field, field_validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    ts: datetime = Field(None, validate_default=True)

    @field_validator('ts', mode='before')
    def set_ts_now(cls, v):
        return v or datetime.now()


print(DemoDataclass())
#> DemoDataclass(ts=datetime.datetime(2032, 1, 2, 3, 4, 5, 6))
print(DemoDataclass(ts='2017-11-08T14:00'))
#> DemoDataclass(ts=datetime.datetime(2017, 11, 8, 14, 0))
```
