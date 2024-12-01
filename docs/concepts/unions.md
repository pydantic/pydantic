Unions are fundamentally different to all other types Pydantic validates - instead of requiring all fields/items/values to be valid, unions require only one member to be valid.

This leads to some nuance around how to validate unions:

* which member(s) of the union should you validate data against, and in which order?
* which errors to raise when validation fails?

Validating unions feels like adding another orthogonal dimension to the validation process.

To solve these problems, Pydantic supports three fundamental approaches to validating unions:

1. [left to right mode](#left-to-right-mode) - the simplest approach, each member of the union is tried in order and the first match is returned
2. [smart mode](#smart-mode) - similar to "left to right mode" members are tried in order; however, validation will proceed past the first match to attempt to find a better match, this is the default mode for most union validation
3. [discriminated unions](#discriminated-unions) - only one member of the union is tried, based on a discriminator

!!! tip

    In general, we recommend using [discriminated unions](#discriminated-unions). They are both more performant and more predictable than untagged unions, as they allow you to control which member of the union to validate against.

    For complex cases, if you're using untagged unions, it's recommended to use `union_mode='left_to_right'` if you need guarantees about the order of validation attempts against the union members.

    If you're looking for incredibly specialized behavior, you can use a [custom validator](../concepts/validators.md#field-validators).

## Union Modes

### Left to Right Mode

!!! note
    Because this mode often leads to unexpected validation results, it is not the default in Pydantic >=2, instead `union_mode='smart'` is the default.

With this approach, validation is attempted against each member of the union in their order they're defined, and the first successful validation is accepted as input.

If validation fails on all members, the validation error includes the errors from all members of the union.

`union_mode='left_to_right'` must be set as a [`Field`](../concepts/fields.md) parameter on union fields where you want to use it.

```python {title="Union with left to right mode"}
from typing import Union

from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    id: Union[str, int] = Field(union_mode='left_to_right')


print(User(id=123))
#> id=123
print(User(id='hello'))
#> id='hello'

try:
    User(id=[])
except ValidationError as e:
    print(e)
    """
    2 validation errors for User
    id.str
      Input should be a valid string [type=string_type, input_value=[], input_type=list]
    id.int
      Input should be a valid integer [type=int_type, input_value=[], input_type=list]
    """
```

The order of members is very important in this case, as demonstrated by tweak the above example:

```python {title="Union with left to right - unexpected results"}
from typing import Union

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Union[int, str] = Field(union_mode='left_to_right')


print(User(id=123))  # (1)
#> id=123
print(User(id='456'))  # (2)
#> id=456
```

1. As expected the input is validated against the `int` member and the result is as expected.
2. We're in lax mode and the numeric string `'123'` is valid as input to the first member of the union, `int`.
   Since that is tried first, we get the surprising result of `id` being an `int` instead of a `str`.

### Smart Mode

Because of the potentially surprising results of `union_mode='left_to_right'`, in Pydantic >=2 the default mode for `Union` validation is `union_mode='smart'`.

In this mode, pydantic attempts to select the best match for the input from the union members. The exact algorithm may change between Pydantic minor releases to allow for improvements in both performance and accuracy.

!!! note

    We reserve the right to tweak the internal `smart` matching algorithm in future versions of Pydantic. If you rely on very specific
    matching behavior, it's recommended to use `union_mode='left_to_right'` or [discriminated unions](#discriminated-unions).

??? info "Smart Mode Algorithm"

    The smart mode algorithm uses two metrics to determine the best match for the input:

    1. The number of valid fields set (relevant for models, dataclasses, and typed dicts)
    2. The exactness of the match (relevant for all types)

    #### Number of valid fields set

    !!! note
        This metric was introduced in Pydantic v2.8.0. Prior to this version, only exactness was used to determine the best match.

    This metric is currently only relevant for models, dataclasses, and typed dicts.

    The greater the number of valid fields set, the better the match. The number of fields set on nested models is also taken into account.
    These counts bubble up to the top-level union, where the union member with the highest count is considered the best match.

    For data types where this metric is relevant, we prioritize this count over exactness. For all other types, we use solely exactness.

    #### Exactness

    For `exactness`, Pydantic scores a match of a union member into one of the following three groups (from highest score to lowest score):

    - An exact type match, for example an `int` input to a `float | int` union validation is an exact type match for the `int` member
    - Validation would have succeeded in [`strict` mode](../concepts/strict_mode.md)
    - Validation would have succeeded in lax mode

    The union match which produced the highest exactness score will be considered the best match.

    In smart mode, the following steps are taken to try to select the best match for the input:

    === "`BaseModel`, `dataclass`, and `TypedDict`"

        1. Union members are attempted left to right, with any successful matches scored into one of the three exactness categories described above,
        with the valid fields set count also tallied.
        2. After all members have been evaluated, the member with the highest "valid fields set" count is returned.
        3. If there's a tie for the highest "valid fields set" count, the exactness score is used as a tiebreaker, and the member with the highest exactness score is returned.
        4. If validation failed on all the members, return all the errors.

    === "All other data types"

        1. Union members are attempted left to right, with any successful matches scored into one of the three exactness categories described above.
            - If validation succeeds with an exact type match, that member is returned immediately and following members will not be attempted.
        2. If validation succeeded on at least one member as a "strict" match, the leftmost of those "strict" matches is returned.
        3. If validation succeeded on at least one member in "lax" mode, the leftmost match is returned.
        4. Validation failed on all the members, return all the errors.

```python
from typing import Union
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: Union[int, str, UUID]
    name: str


user_01 = User(id=123, name='John Doe')
print(user_01)
#> id=123 name='John Doe'
print(user_01.id)
#> 123
user_02 = User(id='1234', name='John Doe')
print(user_02)
#> id='1234' name='John Doe'
print(user_02.id)
#> 1234
user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
#> id=UUID('cf57432e-809e-4353-adbd-9d5c0d733868') name='John Doe'
print(user_03.id)
#> cf57432e-809e-4353-adbd-9d5c0d733868
print(user_03_uuid.int)
#> 275603287559914445491632874575877060712
```

!!! tip
    The type `Optional[x]` is a shorthand for `Union[x, None]`.

    See more details in [Required fields](../concepts/models.md#required-fields).

## Discriminated Unions

**Discriminated unions are sometimes referred to as "Tagged Unions".**

We can use discriminated unions to more efficiently validate `Union` types, by choosing which member of the union to validate against.

This makes validation more efficient and also avoids a proliferation of errors when validation fails.

Adding discriminator to unions also means the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object).

### Discriminated Unions with `str` discriminators

Frequently, in the case of a `Union` with multiple models,
there is a common field to all members of the union that can be used to distinguish
which union case the data should be validated against; this is referred to as the "discriminator" in
[OpenAPI](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/).

To validate models based on that information you can set the same field - let's call it `my_discriminator` -
in each of the models with a discriminated value, which is one (or many) `Literal` value(s).
For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float


class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    scales: bool


class Model(BaseModel):
    pet: Union[Cat, Dog, Lizard] = Field(discriminator='pet_type')
    n: int


print(Model(pet={'pet_type': 'dog', 'barks': 3.14}, n=1))
#> pet=Dog(pet_type='dog', barks=3.14) n=1
try:
    Model(pet={'pet_type': 'dog'}, n=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

### Discriminated Unions with callable `Discriminator`

??? api "API Documentation"
    [`pydantic.types.Discriminator`][pydantic.types.Discriminator]<br>

In the case of a `Union` with multiple models, sometimes there isn't a single uniform field
across all models that you can use as a discriminator.
This is the perfect use case for a callable `Discriminator`.

!!! tip
    When you're designing callable discriminators, remember that you might have to account
    for both `dict` and model type inputs. This pattern is similar to that of `mode='before'` validators,
    where you have to anticipate various forms of input.

    But wait! You ask, I only anticipate passing in `dict` types, why do I need to account for models?
    Pydantic uses callable discriminators for serialization as well, at which point the input to your callable is
    very likely to be a model instance.

    In the following examples, you'll see that the callable discriminators are designed to handle both `dict` and model inputs.
    If you don't follow this practice, it's likely that you'll, in the best case, get warnings during serialization,
    and in the worst case, get runtime errors during validation.

```python
from typing import Any, Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Tag


class Pie(BaseModel):
    time_to_cook: int
    num_ingredients: int


class ApplePie(Pie):
    fruit: Literal['apple'] = 'apple'


class PumpkinPie(Pie):
    filling: Literal['pumpkin'] = 'pumpkin'


def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        return v.get('fruit', v.get('filling'))
    return getattr(v, 'fruit', getattr(v, 'filling', None))


class ThanksgivingDinner(BaseModel):
    dessert: Annotated[
        Union[
            Annotated[ApplePie, Tag('apple')],
            Annotated[PumpkinPie, Tag('pumpkin')],
        ],
        Discriminator(get_discriminator_value),
    ]


apple_variation = ThanksgivingDinner.model_validate(
    {'dessert': {'fruit': 'apple', 'time_to_cook': 60, 'num_ingredients': 8}}
)
print(repr(apple_variation))
"""
ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
"""

pumpkin_variation = ThanksgivingDinner.model_validate(
    {
        'dessert': {
            'filling': 'pumpkin',
            'time_to_cook': 40,
            'num_ingredients': 6,
        }
    }
)
print(repr(pumpkin_variation))
"""
ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
"""
```

`Discriminator`s can also be used to validate `Union` types with combinations of models and primitive types.

For example:

```python
from typing import Any, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Tag, ValidationError


def model_x_discriminator(v: Any) -> str:
    if isinstance(v, int):
        return 'int'
    if isinstance(v, (dict, BaseModel)):
        return 'model'
    else:
        # return None if the discriminator value isn't found
        return None


class SpecialValue(BaseModel):
    value: int


class DiscriminatedModel(BaseModel):
    value: Annotated[
        Union[
            Annotated[int, Tag('int')],
            Annotated['SpecialValue', Tag('model')],
        ],
        Discriminator(model_x_discriminator),
    ]


model_data = {'value': {'value': 1}}
m = DiscriminatedModel.model_validate(model_data)
print(m)
#> value=SpecialValue(value=1)

int_data = {'value': 123}
m = DiscriminatedModel.model_validate(int_data)
print(m)
#> value=123

try:
    DiscriminatedModel.model_validate({'value': 'not an int or a model'})
except ValidationError as e:
    print(e)  # (1)!
    """
    1 validation error for DiscriminatedModel
    value
      Unable to extract tag using discriminator model_x_discriminator() [type=union_tag_not_found, input_value='not an int or a model', input_type=str]
    """
```

1. Notice the callable discriminator function returns `None` if a discriminator value is not found.
   When `None` is returned, this `union_tag_not_found` error is raised.

!!! note
    Using the [[`typing.Annotated`][] fields syntax](../concepts/types.md#composing-types-via-annotated) can be handy to regroup
    the `Union` and `discriminator` information. See the next example for more details.

    There are a few ways to set a discriminator for a field, all varying slightly in syntax.

    For `str` discriminators:
    ```
    some_field: Union[...] = Field(discriminator='my_discriminator'
    some_field: Annotated[Union[...], Field(discriminator='my_discriminator')]
    ```

    For callable `Discriminator`s:
    ```
    some_field: Union[...] = Field(discriminator=Discriminator(...))
    some_field: Annotated[Union[...], Discriminator(...)]
    some_field: Annotated[Union[...], Field(discriminator=Discriminator(...))]
    ```

!!! warning
    Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

    Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to
    distinguish fields of `Union[T]` from `T`.

### Nested Discriminated Unions

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
You can do it by creating nested `Annotated` types, e.g.:

```python
from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str


class WhiteCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str


Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]


class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str


Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]


class Model(BaseModel):
    pet: Pet
    n: int


m = Model(pet={'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}, n=1)
print(m)
#> pet=BlackCat(pet_type='cat', color='black', black_name='felix') n=1
try:
    Model(pet={'pet_type': 'cat', 'color': 'red'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat.black.black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```

!!! tip
    If you want to validate data against a union, and solely a union, you can use pydantic's [`TypeAdapter`](../concepts/type_adapter.md) construct instead of inheriting from the standard `BaseModel`.

    In the context of the previous example, we have the following:

    ```python {lint="skip" test="skip"}
    type_adapter = TypeAdapter(Pet)

    pet = type_adapter.validate_python(
        {'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}
    )
    print(repr(pet))
    #> BlackCat(pet_type='cat', color='black', black_name='felix')
    ```

## Union Validation Errors

When `Union` validation fails, error messages can be quite verbose, as they will produce validation errors for
each case in the union.
This is especially noticeable when dealing with recursive models, where reasons may be generated at each level of
recursion.
Discriminated unions help to simplify error messages in this case, as validation errors are only produced for
the case with a matching discriminator value.

You can also customize the error type, message, and context for a `Discriminator` by passing
these specifications as parameters to the `Discriminator` constructor, as seen in the example below.

```python
from typing import Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Tag, ValidationError


# Errors are quite verbose with a normal Union:
class Model(BaseModel):
    x: Union[str, 'Model']


try:
    Model.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': 1}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': 1}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    x.Model.x.Model.x.Model
      Input should be a valid dictionary or instance of Model [type=model_type, input_value=1, input_type=int]
    """

try:
    Model.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': {}}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': {}}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value={}, input_type=dict]
    x.Model.x.Model.x.Model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """


# Errors are much simpler with a discriminated union:
def model_x_discriminator(v):
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (dict, BaseModel)):
        return 'model'


class DiscriminatedModel(BaseModel):
    x: Annotated[
        Union[
            Annotated[str, Tag('str')],
            Annotated['DiscriminatedModel', Tag('model')],
        ],
        Discriminator(
            model_x_discriminator,
            custom_error_type='invalid_union_member',  # (1)!
            custom_error_message='Invalid union member',  # (2)!
            custom_error_context={'discriminator': 'str_or_model'},  # (3)!
        ),
    ]


try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x
      Invalid union member [type=invalid_union_member, input_value=1, input_type=int]
    """

try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x.model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """

# The data is still handled properly when valid:
data = {'x': {'x': {'x': 'a'}}}
m = DiscriminatedModel.model_validate(data)
print(m.model_dump())
#> {'x': {'x': {'x': 'a'}}}
```

1. `custom_error_type` is the `type` attribute of the `ValidationError` raised when validation fails.
2. `custom_error_message` is the `msg` attribute of the `ValidationError` raised when validation fails.
3. `custom_error_context` is the `ctx` attribute of the `ValidationError` raised when validation fails.

You can also simplify error messages by labeling each case with a [`Tag`][pydantic.types.Tag].
This is especially useful when you have complex types like those in this example:

```python
from typing import Dict, List, Union

from typing_extensions import Annotated

from pydantic import AfterValidator, Tag, TypeAdapter, ValidationError

DoubledList = Annotated[List[int], AfterValidator(lambda x: x * 2)]
StringsMap = Dict[str, str]


# Not using any `Tag`s for each union case, the errors are not so nice to look at
adapter = TypeAdapter(Union[DoubledList, StringsMap])

try:
    adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]
    function-after[<lambda>(), list[int]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    dict[str,str]
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """

tag_adapter = TypeAdapter(
    Union[
        Annotated[DoubledList, Tag('DoubledList')],
        Annotated[StringsMap, Tag('StringsMap')],
    ]
)

try:
    tag_adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[DoubledList,StringsMap]
    DoubledList.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    StringsMap
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """
```
