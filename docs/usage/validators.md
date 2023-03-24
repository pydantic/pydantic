Custom validation and complex relationships between objects can be achieved using the `validator` decorator.

```py
from pydantic import BaseModel, ValidationError, validator


class UserModel(BaseModel):
    name: str
    username: str
    password1: str
    password2: str

    @validator('name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('passwords do not match')
        return v

    @validator('username')
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

try:
    UserModel(
        name='samuel',
        username='scolvin',
        password1='zxcvbn',
        password2='zxcvbn2',
    )
except ValidationError as e:
    print(e)
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
from pydantic import BaseModel, ValidationError, validator


class DemoModel(BaseModel):
    square_numbers: List[int] = []
    cube_numbers: List[int] = []

    # '*' is the same as 'cube_numbers', 'square_numbers' here:
    @validator('*', pre=True)
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split('|')
        return v

    @validator('cube_numbers', 'square_numbers')
    def check_sum(cls, v):
        if sum(v) > 42:
            raise ValueError('sum of numbers greater than 42')
        return v

    @validator('square_numbers', each_item=True)
    def check_squares(cls, v):
        assert v**0.5 % 1 == 0, f'{v} is not a square number'
        return v

    @validator('cube_numbers', each_item=True)
    def check_cubes(cls, v):
        # 64 ** (1 / 3) == 3.9999999999999996 (!)
        # this is not a good way of checking cubes
        assert v ** (1 / 3) % 1 == 0, f'{v} is not a cubed number'
        return v


print(DemoModel(square_numbers=[1, 4, 9]))
print(DemoModel(square_numbers='1|4|16'))
print(DemoModel(square_numbers=[16], cube_numbers=[8, 27]))
try:
    DemoModel(square_numbers=[1, 4, 2])
except ValidationError as e:
    print(e)

try:
    DemoModel(cube_numbers=[27, 27])
except ValidationError as e:
    print(e)
```

A few more things to note:

* a single validator can be applied to multiple fields by passing it multiple field names
* a single validator can also be called on *all* fields by passing the special value `'*'`
* the keyword argument `pre` will cause the validator to be called prior to other validation
* passing `each_item=True` will result in the validator being applied to individual values
  (e.g. of `List`, `Dict`, `Set`, etc.), rather than the whole object

## Subclass Validators and `each_item`

If using a validator with a subclass that references a `List` type field on a parent class, using `each_item=True` will
cause the validator not to run; instead, the list must be iterated over programmatically.

```py
from typing import List
from pydantic import BaseModel, ValidationError, validator


class ParentModel(BaseModel):
    names: List[str]


class ChildModel(ParentModel):
    @validator('names', each_item=True)
    def check_names_not_empty(cls, v):
        assert v != '', 'Empty strings are not allowed.'
        return v


# This will NOT raise a ValidationError because the validator was not called
try:
    child = ChildModel(names=['Alice', 'Bob', 'Eve', ''])
except ValidationError as e:
    print(e)
else:
    print('No ValidationError caught.')


class ChildModel2(ParentModel):
    @validator('names')
    def check_names_not_empty(cls, v):
        for name in v:
            assert name != '', 'Empty strings are not allowed.'
        return v


try:
    child = ChildModel2(names=['Alice', 'Bob', 'Eve', ''])
except ValidationError as e:
    print(e)
```

## Validate Always

For performance reasons, by default validators are not called for fields when a value is not supplied.
However there are situations where it may be useful or required to always call the validator, e.g.
to set a dynamic default value.

```py
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
from pydantic import BaseModel, validator


def normalize(name: str) -> str:
    return ' '.join((word.capitalize()) for word in name.split(' '))


class Producer(BaseModel):
    name: str

    # validators
    _normalize_name = validator('name', allow_reuse=True)(normalize)


class Consumer(BaseModel):
    name: str

    # validators
    _normalize_name = validator('name', allow_reuse=True)(normalize)


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

## Root Validators

Validation can also be performed on the entire model's data.

```py
from pydantic import BaseModel, ValidationError, root_validator


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str

    @root_validator(pre=True)
    def check_card_number_omitted(cls, values):
        assert 'card_number' not in values, 'card_number should not be included'
        return values

    @root_validator(skip_on_failure=True)
    def check_passwords_match(cls, values):
        pw1, pw2 = values.get('password1'), values.get('password2')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        return values


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

```py
from datetime import datetime

from pydantic import validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    ts: datetime = None

    @validator('ts', pre=True, always=True)
    def set_ts_now(cls, v):
        return v or datetime.now()


print(DemoDataclass())
print(DemoDataclass(ts='2017-11-08T14:00'))
```
