---
description: Support for a model attribute to accept different types.
---

The `Union` type allows a model attribute to accept different types, e.g.:

!!! info
    You may get unexpected coercion with `Union`; see below.<br />
    Know that you can also make the check slower but stricter by using [Smart Union](model_config.md#smart-union)

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

However, as can be seen above, *pydantic* will attempt to 'match' any of the types defined under `Union` and will use
the first one that matches. In the above example the `id` of `user_03` was defined as a `uuid.UUID` class (which
is defined under the attribute's `Union` annotation) but as the `uuid.UUID` can be marshalled into an `int` it
chose to match against the `int` type and disregarded the other types.

!!! warning
    `typing.Union` also ignores order when [defined](https://docs.python.org/3/library/typing.html#typing.Union),
    so `Union[int, float] == Union[float, int]` which can lead to unexpected behaviour
    when combined with matching based on the `Union` type order inside other type definitions, such as `List` and `Dict`
    types (because Python treats these definitions as singletons).
    For example, `Dict[str, Union[int, float]] == Dict[str, Union[float, int]]` with the order based on the first time it was defined.
    Please note that this can also be [affected by third party libraries](https://github.com/pydantic/pydantic/issues/2835)
    and their internal type definitions and the import orders.

As such, it is recommended that, when defining `Union` annotations, the most specific type is included first and
followed by less specific types.

In the above example, the `UUID` class should precede the `int` and `str` classes to preclude the unexpected representation as such:

```py
from typing import Union
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: Union[UUID, int, str]
    name: str


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

    `Optional[x]` can also be used to specify a required field that can take `None` as a value.

    See more details in [Required Fields](models.md#required-fields).

#### Discriminated Unions (a.k.a. Tagged Unions)

When `Union` is used with multiple submodels, you sometimes know exactly which submodel needs to
be checked and validated and want to enforce this.
To do that you can set the same field - let's call it `my_discriminator` - in each of the submodels
with a discriminated value, which is one (or many) `Literal` value(s).
For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

Setting a discriminated union has many benefits:

- validation is faster since it is only attempted against one model
- only one explicit error is raised in case of failure
- the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#discriminatorObject)

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
    1 validation error for Lizard
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

!!! note
    Using the [Annotated Fields syntax](../schema/#typingannotated-fields) can be handy to regroup
    the `Union` and `discriminator` information. See below for an example!

!!! warning
    Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

    Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to
    distinguish fields of `Union[T]` from `T`.

#### Nested Discriminated Unions

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
In this case you can always create "intermediate" models with `__root__` and add your discriminator.

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


# Can also be written with a custom root type
#
# class Cat(BaseModel):
#   __root__: Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

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
    1 validation error for Dog
    pet.cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Dog
    pet.cat.black.black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```
