Unions are fundamentally different to all other types Pydantic validates - instead of requiring all fields/items/values to be valid, unions require only one member to be valid.

This leads to some nuance around how to validate unions:
* which member(s) of the union should you validate data against, and in which order?
* which errors to raise when validation fails?

Validating unions feels like adding another orthogonal dimension to the validation process.

To solve these problems, Pydantic supports three fundamental approaches to validating unions:
1. [left to right mode](#left-to-right-mode) - the simplest approach, each member of the union is tried in order
2. [smart mode](#smart-mode) - as with "left to right mode" all members are tried, but strict validation is used to try to find the best match
3. [discriminated unions](#discriminated-unions) - only one member of the union is tried, based on a discriminator

## Union Modes

### Left to Right Mode

!!! note
    Because this mode often leads to unexpected validation results, it is not the default in Pydantic >=2, instead `union_mode='smart'` is the default.

With this approach, validation is attempted against each member of the union in their order they're defined, and the first successful validation is accepted as input.

If validation fails on all members, the validation error includes the errors from all members of the union.

`union_mode='left_to_right'` must be set as a [`Field`](../concepts/fields.md) parameter on union fields where you want to use it.

```py title="Union with left to right mode"
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

```py title="Union with left to right - unexpected results"
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

Because of the surprising side effects of `union_mode='left_to_right'`, in Pydantic >=2 the default mode for `Union` validation is `union_mode='smart'`.

In this mode, the following steps are take to try to select the best match for the input:
1. Validation is first attempted in [`strict` mode](../concepts/strict_mode.md) against each member of the union in the order they're defined.
2. If validation succeeds on any member, that member is accepted as input.
3. If validation fails on all members, validation is attempted again in [`lax` mode](../concepts/strict_mode.md) against each member of the union in the order they're defined.
4. If validation succeeds on any member, that member is accepted as input.
5. If validation fails on all members, all errors from lax validation are returned.

```py
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

Add ing disciminator to unions also means the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object)

### Discriminated Unions with `str` discriminators

Frequently, in the case of a `Union` with multiple models,
there is a common field to all members of the union that can be used to distinguish
which union case the data should be validated against; this is referred to as the "discriminator" in
[OpenAPI](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/).

To validate models based on that information you can set the same field - let's call it `my_discriminator` -
in each of the models with a discriminated value, which is one (or many) `Literal` value(s).
For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

```py requires="3.8"
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
    pet: Union[Cat, Dog, Lizard] = Field(..., discriminator='pet_type')
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

### Discriminated Unions with `CallableDiscriminator` discriminators

In the case of a `Union` with multiple models, sometimes there isn't a single uniform field
across all models that you can use as a discriminator. This is the perfect use case for the `CallableDiscriminator` approach.

```py requires="3.8"
from typing import Any, Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, CallableDiscriminator, Tag


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
        CallableDiscriminator(get_discriminator_value),
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

`CallableDiscriminators` can also be used to validate `Union` types with combinations of models and primitive types.

For example:

```py requires="3.8"
from typing import Any, Union

from typing_extensions import Annotated

from pydantic import BaseModel, CallableDiscriminator, Tag


def model_x_discriminator(v: Any) -> str:
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
        CallableDiscriminator(
            model_x_discriminator,
            custom_error_type='invalid_union_member',
            custom_error_message='Invalid union member',
            custom_error_context={'discriminator': 'str_or_model'},
        ),
    ]


data = {'x': {'x': {'x': 'a'}}}
m = DiscriminatedModel.model_validate(data)
assert m == (
    DiscriminatedModel(x=DiscriminatedModel(x=DiscriminatedModel(x='a')))
)
assert m.model_dump() == data
```

!!! note
    Using the [`typing.Annotated` fields syntax](../concepts/json_schema.md#typingannotated-fields) can be handy to regroup
    the `Union` and `discriminator` information. See the next example for more details.

    There are a few ways to set a discriminator for a field, all varying slightly in syntax.

    For `str` discriminators:
    ```
    some_field: Union[...] = Field(discriminator='my_discriminator'
    some_field: Annotated[Union[...], Field(discriminator='my_discriminator')]
    ```

    For `CallableDiscriminator` discriminators:
    ```
    some_field: Union[...] = Field(discriminator=CallableDiscriminator(...))
    some_field: Annotated[Union[...], CallableDiscriminator(...)]
    some_field: Annotated[Union[...], Field(discriminator=CallableDiscriminator(...))]
    ```

!!! warning
    Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

    Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to
    distinguish fields of `Union[T]` from `T`.

### Nested Discriminated Unions

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
You can do it by creating nested `Annotated` types, e.g.:

```py requires="3.8"
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

## Union Validation Errors

When validation fails, error messages can be quite verbose, especially when you're not using discriminated unions.
The below example shows the benefits of using discriminated unions in terms of error message simplicity.

```py
from typing import Union

from typing_extensions import Annotated

from pydantic import BaseModel, CallableDiscriminator, Tag, ValidationError


# Errors are quite verbose with a normal Union:
class Model(BaseModel):
    x: Union[str, 'Model']


try:
    Model.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as exc_info:
    assert exc_info.errors(include_url=False) == [
        {
            'input': {'x': {'x': 1}},
            'loc': ('x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': {'x': 1},
            'loc': ('x', 'Model', 'x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': 1,
            'loc': ('x', 'Model', 'x', 'Model', 'x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'ctx': {'class_name': 'Model'},
            'input': 1,
            'loc': ('x', 'Model', 'x', 'Model', 'x', 'Model'),
            'msg': 'Input should be a valid dictionary or instance of Model',
            'type': 'model_type',
        },
    ]

try:
    Model.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as exc_info:
    assert exc_info.errors(include_url=False) == [
        {
            'input': {'x': {'x': {}}},
            'loc': ('x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': {'x': {}},
            'loc': ('x', 'Model', 'x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': {},
            'loc': ('x', 'Model', 'x', 'Model', 'x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': {},
            'loc': ('x', 'Model', 'x', 'Model', 'x', 'Model', 'x'),
            'msg': 'Field required',
            'type': 'missing',
        },
    ]


# Errors are much more simple with a discriminated union:
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
        CallableDiscriminator(
            model_x_discriminator,
            custom_error_type='invalid_union_member',
            custom_error_message='Invalid union member',
            custom_error_context={'discriminator': 'str_or_model'},
        ),
    ]


try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as exc_info:
    assert exc_info.errors(include_url=False) == [
        {
            'ctx': {'discriminator': 'str_or_model'},
            'input': 1,
            'loc': ('x', 'model', 'x', 'model', 'x'),
            'msg': 'Invalid union member',
            'type': 'invalid_union_member',
        }
    ]

try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as exc_info:
    assert exc_info.errors(include_url=False) == [
        {
            'input': {},
            'loc': ('x', 'model', 'x', 'model', 'x', 'model', 'x'),
            'msg': 'Field required',
            'type': 'missing',
        }
    ]

# The data is still handled properly when valid:
data = {'x': {'x': {'x': 'a'}}}
m = DiscriminatedModel.model_validate(data)
assert m == DiscriminatedModel(
    x=DiscriminatedModel(x=DiscriminatedModel(x='a'))
)
assert m.model_dump() == data
```

You can also simplify error messages by labeling each case with a [`Tag`][pydantic.types.Tag].
This is especially useful when you have complex types like those in this example:

```py
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
    assert (
        '2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]'
        in str(exc_info)
    )

    # the loc's are bad here:
    assert exc_info.errors() == [
        {
            'input': 'a',
            'loc': ('function-after[<lambda>(), list[int]]', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an '
            'integer',
            'type': 'int_parsing',
            'url': 'https://errors.pydantic.dev/2.4/v/int_parsing',
        },
        {
            'input': ['a'],
            'loc': ('dict[str,str]',),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
            'url': 'https://errors.pydantic.dev/2.4/v/dict_type',
        },
    ]


tag_adapter = TypeAdapter(
    Union[
        Annotated[DoubledList, Tag('DoubledList')],
        Annotated[StringsMap, Tag('StringsMap')],
    ]
)

try:
    tag_adapter.validate_python(['a'])
except ValidationError as exc_info:
    assert '2 validation errors for union[DoubledList,StringsMap]' in str(
        exc_info
    )

    # the loc's are good here:
    assert exc_info.errors() == [
        {
            'input': 'a',
            'loc': ('DoubledList', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an '
            'integer',
            'type': 'int_parsing',
            'url': 'https://errors.pydantic.dev/2.4/v/int_parsing',
        },
        {
            'input': ['a'],
            'loc': ('StringsMap',),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
            'url': 'https://errors.pydantic.dev/2.4/v/dict_type',
        },
    ]
```
