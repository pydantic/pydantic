!!! warning
    This page still needs to be updated for v2.0.

## Field validators

??? api "API Documentation"
    [`pydantic.functional_validators.field_validator`][pydantic.functional_validators.field_validator]<br>

Custom validation and complex relationships between objects can be achieved using the `@field_validator` decorator.

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
"""
name='Samuel Colvin' username='scolvin' password1='zxcvbn' password2='zxcvbn'
"""

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
* the second argument is the field value to validate; it can be named as you please
* the third argument is an instance of `pydantic.FieldValidationInfo`
* validators should either return the parsed value or raise a `ValueError` or `AssertionError`
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

## Annotated Validators

??? api "API Documentation"
    [`pydantic.functional_validators.WrapValidator`][pydantic.functional_validators.WrapValidator]<br>
    [`pydantic.functional_validators.PlainValidator`][pydantic.functional_validators.PlainValidator]<br>
    [`pydantic.functional_validators.BeforeValidator`][pydantic.functional_validators.BeforeValidator]<br>
    [`pydantic.functional_validators.AfterValidator`][pydantic.functional_validators.AfterValidator]<br>

Pydantic also provides a way to apply validators via use of `Annotated`.

!!! note
    You can use multiple before, after, or wrap validators, but only one `PlainValidator` since a plain validator
    will not call any inner validators.

```py
from typing import List

from typing_extensions import Annotated

from pydantic import BaseModel, ValidationError, field_validator
from pydantic.functional_validators import AfterValidator


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

!!! note "Validation order"
    Validation order matters. Within a given type, validation goes from right to left and back. That is, it goes
    from right to left running all "before" validators (or calling into "wrap" validators), then left to right back out calling all "after" validators.

    In the following example, `func2` will be called before `func1`.

    ```py test="skip" lint="skip" upgrade="skip"
    MyVal = Annotated[int, AfterValidator(func1), BeforeValidator(func2)]
    ```

A few more things to note:

* A single validator can be applied to multiple fields by passing it multiple field names.
* A single validator can also be called on *all* fields by passing the special value `'*'`.
* The keyword argument `mode='before'` will cause the validator to be called prior to other validation.
* Using validator annotations inside of `Annotated` allows applying validators to items of collections.

## Special Types

Pydantic provides a few special types that can be used to customize validation.

- [`InstanceOf`][pydantic.functional_validators.InstanceOf] is a type that can be used to validate that a value is an instance of a given class.

```py
from typing import List

from pydantic import BaseModel, InstanceOf, ValidationError


class Fruit:
    def __repr__(self):
        return self.__class__.__name__


class Banana(Fruit):
    ...


class Apple(Fruit):
    ...


class Basket(BaseModel):
    fruits: List[InstanceOf[Fruit]]


print(Basket(fruits=[Banana(), Apple()]))
#> fruits=[Banana, Apple]
try:
    Basket(fruits=[Banana(), 'Apple'])
except ValidationError as e:
    print(e)
    """
    1 validation error for Basket
    fruits.1
      Input should be an instance of Fruit [type=is_instance_of, input_value='Apple', input_type=str]
    """
```

- [`SkipValidation`][pydantic.functional_validators.SkipValidation] is a type that can be used to skip validation on a field.

```py
from typing import List

from pydantic import BaseModel, SkipValidation


class Model(BaseModel):
    names: List[SkipValidation[str]]


m = Model(names=['foo', 'bar'])
print(m)
#> names=['foo', 'bar']

m = Model(names=['foo', 123])  # (1)!
print(m)
#> names=['foo', 123]
```

1. Note that the validation of the second item is skipped.

### Generic validated collections

To validate individual items of a collection (list, dict, etc.) field you can use `Annotated` to apply validators to the inner items.
In this example we also use type aliases to create a generic validated collection to demonstrate how this approach leads to composability and coda re-use.

```py
from typing import List, TypeVar

from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator

T = TypeVar('T')

SortedList = Annotated[List[T], AfterValidator(lambda x: sorted(x))]

Name = Annotated[str, AfterValidator(lambda x: x.title())]


class DemoModel(BaseModel):
    int_list: SortedList[int]
    name_list: SortedList[Name]


print(DemoModel(int_list=[3, 2, 1], name_list=['adrian g', 'David']))
#> int_list=[1, 2, 3] name_list=['Adrian G', 'David']
```

### Wrap validators

Wrap validators are useful for cases where you want to validate a value, but also want to return a default value if validation fails.

```py
from datetime import datetime

from typing_extensions import Annotated

from pydantic import BaseModel, ValidationError, WrapValidator


def validate_timestamp(v, handler):
    if v == 'now':
        # we don't want to bother with further validation, just return the new value
        return datetime.now()
    try:
        return handler(v)
    except ValidationError:
        # validation failed, in this case we want to return a default value
        return datetime(2000, 1, 1)


MyTimestamp = Annotated[datetime, WrapValidator(validate_timestamp)]


class Model(BaseModel):
    a: MyTimestamp


print(Model(a='now').a)
#> 2032-01-02 03:04:05.000006
print(Model(a='invalid').a)
#> 2000-01-01 00:00:00
```

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

## Model validators

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
    def check_passwords_match(self) -> 'UserModel':
        pw1 = self.password1
        pw2 = self.password2
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        return self


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

## Field checks

During class creation, validators are checked to confirm that the fields they specify actually exist on the model.

This may be undesirable if, for example, you want to define a validator to validate fields that will only be present
on subclasses of the model where the validator is defined.

If you want to disable these checks during class creation, you can pass `check_fields=False` as a keyword argument to
the validator.

## Dataclass validators

Validators also work with Pydantic dataclasses.

```py
from pydantic import field_validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    product_id: str  # should be a five-digit string, may have leading zeros

    @field_validator('product_id', mode='before')
    @classmethod
    def convert_int_serial(cls, v):
        if isinstance(v, int):
            v = str(v).zfill(5)
        return v


print(DemoDataclass(product_id='01234'))
#> DemoDataclass(product_id='01234')
print(DemoDataclass(product_id=2468))
#> DemoDataclass(product_id='02468')
```

## Validation Context

You can pass a context object to the validation methods which can be accessed from the `info`
argument to decorated validator functions:

```python
from pydantic import BaseModel, FieldValidationInfo, field_validator


class Model(BaseModel):
    text: str

    @field_validator('text')
    @classmethod
    def remove_stopwords(cls, v: str, info: FieldValidationInfo):
        context = info.context
        if context:
            stopwords = context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


data = {'text': 'This is an example document'}
print(Model.model_validate(data))  # no context
#> text='This is an example document'
print(Model.model_validate(data, context={'stopwords': ['this', 'is', 'an']}))
#> text='example document'
print(Model.model_validate(data, context={'stopwords': ['document']}))
#> text='This is an example'
```

This is useful when you need to dynamically update the validation behavior during runtime. For example, if you wanted
a field to have a dynamically controllable set of allowed values, this could be done by passing the allowed values
by context, and having a separate mechanism for updating what is allowed:

```python
from typing import Any, Dict, List

from pydantic import (
    BaseModel,
    FieldValidationInfo,
    ValidationError,
    field_validator,
)

_allowed_choices = ['a', 'b', 'c']


def set_allowed_choices(allowed_choices: List[str]) -> None:
    global _allowed_choices
    _allowed_choices = allowed_choices


def get_context() -> Dict[str, Any]:
    return {'allowed_choices': _allowed_choices}


class Model(BaseModel):
    choice: str

    @field_validator('choice')
    @classmethod
    def validate_choice(cls, v: str, info: FieldValidationInfo):
        allowed_choices = info.context.get('allowed_choices')
        if allowed_choices and v not in allowed_choices:
            raise ValueError(f'choice must be one of {allowed_choices}')
        return v


print(Model.model_validate({'choice': 'a'}, context=get_context()))
#> choice='a'

try:
    print(Model.model_validate({'choice': 'd'}, context=get_context()))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    choice
      Value error, choice must be one of ['a', 'b', 'c'] [type=value_error, input_value='d', input_type=str]
    """

set_allowed_choices(['b', 'c'])

try:
    print(Model.model_validate({'choice': 'a'}, context=get_context()))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    choice
      Value error, choice must be one of ['b', 'c'] [type=value_error, input_value='a', input_type=str]
    """
```

### Using validation context with `BaseModel` initialization
Although there is no way to specify a context in the standard `BaseModel` initializer, you can work around this through
the use of `contextvars.ContextVar` and a custom `__init__` method:

```python
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator

from pydantic import BaseModel, FieldValidationInfo, field_validator

_init_context_var = ContextVar('_init_context_var', default=None)


@contextmanager
def init_context(value: Dict[str, Any]) -> Iterator[None]:
    token = _init_context_var.set(value)
    try:
        yield
    finally:
        _init_context_var.reset(token)


class Model(BaseModel):
    my_number: int

    def __init__(__pydantic_self__, **data: Any) -> None:
        __pydantic_self__.__pydantic_validator__.validate_python(
            data,
            self_instance=__pydantic_self__,
            context=_init_context_var.get(),
        )

    @field_validator('my_number')
    @classmethod
    def multiply_with_context(
        cls, value: int, info: FieldValidationInfo
    ) -> int:
        if info.context:
            multiplier = info.context.get('multiplier', 1)
            value = value * multiplier
        return value


print(Model(my_number=2))
#> my_number=2

with init_context({'multiplier': 3}):
    print(Model(my_number=2))
    #> my_number=6

print(Model(my_number=2))
#> my_number=2
```
