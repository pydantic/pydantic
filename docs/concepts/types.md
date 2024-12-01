Where possible Pydantic uses [standard library types](../api/standard_library_types.md) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so Pydantic implements many commonly used types.

There are also more complex types that can be found in the
[Pydantic Extra Types](https://github.com/pydantic/pydantic-extra-types) package.

If no existing type suits your purpose you can also implement your [own Pydantic-compatible types](#custom-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.


* [Standard Library Types](../api/standard_library_types.md) &mdash; types from the Python standard library.
* [Strict Types](#strict-types) &mdash; types that enable you to prevent coercion from compatible types.
* [Custom Data Types](#custom-types) &mdash; create your own custom data types.
* [Field Type Conversions](../concepts/conversion_table.md) &mdash; strict and lax conversion between different field types.


## Type conversion

During validation, Pydantic can coerce data into expected types.

There are two modes of coercion: strict and lax. See [Conversion Table](../concepts/conversion_table.md) for more details on how Pydantic converts data in both strict and lax modes.

See [Strict mode](../concepts/strict_mode.md) and [Strict Types](#strict-types) for details on enabling strict coercion.


## Strict Types

Pydantic provides the following strict types:

- [`StrictBool`][pydantic.types.StrictBool]
- [`StrictBytes`][pydantic.types.StrictBytes]
- [`StrictFloat`][pydantic.types.StrictFloat]
- [`StrictInt`][pydantic.types.StrictInt]
- [`StrictStr`][pydantic.types.StrictStr]

These types will only pass validation when the validated value is of the respective type or is a subtype of that type.

### Constrained types

This behavior is also exposed via the `strict` field of the constrained types and can be combined with a multitude of complex validation rules. See the individual type signatures for supported arguments.

- [`conbytes()`][pydantic.types.conbytes]
- [`condate()`][pydantic.types.condate]
- [`condecimal()`][pydantic.types.condecimal]
- [`confloat()`][pydantic.types.confloat]
- [`confrozenset()`][pydantic.types.confrozenset]
- [`conint()`][pydantic.types.conint]
- [`conlist()`][pydantic.types.conlist]
- [`conset()`][pydantic.types.conset]
- [`constr()`][pydantic.types.constr]

The following caveats apply:

- `StrictBytes` (and the `strict` option of `conbytes()`) will accept both `bytes`,
   and `bytearray` types.
- `StrictInt` (and the `strict` option of `conint()`) will not accept `bool` types,
    even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `confloat()`) will not accept `int`.

Besides the above, you can also have a [`FiniteFloat`][pydantic.types.FiniteFloat] type that will only accept finite values (i.e. not `inf`, `-inf` or `nan`).


## Custom Types

You can also define your own custom data types. There are several ways to achieve it.

### Composing types via `Annotated`

[PEP 593] introduced `Annotated` as a way to attach runtime metadata to types without changing how type checkers interpret them.
Pydantic takes advantage of this to allow you to create types that are identical to the original type as far as type checkers are concerned, but add validation, serialize differently, etc.

For example, to create a type representing a positive int:

```python
# or `from typing import Annotated` for Python 3.9+
from typing_extensions import Annotated

from pydantic import Field, TypeAdapter, ValidationError

PositiveInt = Annotated[int, Field(gt=0)]

ta = TypeAdapter(PositiveInt)

print(ta.validate_python(1))
#> 1

try:
    ta.validate_python(-1)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for constrained-int
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```

Note that you can also use constraints from [annotated-types](https://github.com/annotated-types/annotated-types)
to make this Pydantic-agnostic:

```python
from annotated_types import Gt
from typing_extensions import Annotated

from pydantic import TypeAdapter, ValidationError

PositiveInt = Annotated[int, Gt(0)]

ta = TypeAdapter(PositiveInt)

print(ta.validate_python(1))
#> 1

try:
    ta.validate_python(-1)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for constrained-int
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```

#### Adding validation and serialization

You can add or override validation, serialization, and JSON schemas to an arbitrary type using the markers that
Pydantic exports:

```python
from typing_extensions import Annotated

from pydantic import (
    AfterValidator,
    PlainSerializer,
    TypeAdapter,
    WithJsonSchema,
)

TruncatedFloat = Annotated[
    float,
    AfterValidator(lambda x: round(x, 1)),
    PlainSerializer(lambda x: f'{x:.1e}', return_type=str),
    WithJsonSchema({'type': 'string'}, mode='serialization'),
]


ta = TypeAdapter(TruncatedFloat)

input = 1.02345
assert input != 1.0

assert ta.validate_python(input) == 1.0

assert ta.dump_json(input) == b'"1.0e+00"'

assert ta.json_schema(mode='validation') == {'type': 'number'}
assert ta.json_schema(mode='serialization') == {'type': 'string'}
```

#### Generics

You can use type variables within `Annotated` to make reusable modifications to types:

```python
from typing import Any, List, Sequence, TypeVar

from annotated_types import Gt, Len
from typing_extensions import Annotated

from pydantic import ValidationError
from pydantic.type_adapter import TypeAdapter

SequenceType = TypeVar('SequenceType', bound=Sequence[Any])


ShortSequence = Annotated[SequenceType, Len(max_length=10)]


ta = TypeAdapter(ShortSequence[List[int]])

v = ta.validate_python([1, 2, 3, 4, 5])
assert v == [1, 2, 3, 4, 5]

try:
    ta.validate_python([1] * 100)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[int]
      List should have at most 10 items after validation, not 100 [type=too_long, input_value=[1, 1, 1, 1, 1, 1, 1, 1, ... 1, 1, 1, 1, 1, 1, 1, 1], input_type=list]
    """


T = TypeVar('T')  # or a bound=SupportGt

PositiveList = List[Annotated[T, Gt(0)]]

ta = TypeAdapter(PositiveList[float])

v = ta.validate_python([1])
assert type(v[0]) is float


try:
    ta.validate_python([-1])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[constrained-float]
    0
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```

### Named type aliases

The above examples make use of implicit type aliases.
This means that they will not be able to have a `title` in JSON schemas and their schema will be copied between fields.
You can use [PEP 695]'s `TypeAliasType` via its [typing-extensions] backport to make named aliases, allowing you to define a new type without creating subclasses.
This new type can be as simple as a name or have complex validation logic attached to it:

```python
from typing import List

from annotated_types import Gt
from typing_extensions import Annotated, TypeAliasType

from pydantic import BaseModel

ImplicitAliasPositiveIntList = List[Annotated[int, Gt(0)]]


class Model1(BaseModel):
    x: ImplicitAliasPositiveIntList
    y: ImplicitAliasPositiveIntList


print(Model1.model_json_schema())
"""
{
    'properties': {
        'x': {
            'items': {'exclusiveMinimum': 0, 'type': 'integer'},
            'title': 'X',
            'type': 'array',
        },
        'y': {
            'items': {'exclusiveMinimum': 0, 'type': 'integer'},
            'title': 'Y',
            'type': 'array',
        },
    },
    'required': ['x', 'y'],
    'title': 'Model1',
    'type': 'object',
}
"""

PositiveIntList = TypeAliasType('PositiveIntList', List[Annotated[int, Gt(0)]])


class Model2(BaseModel):
    x: PositiveIntList
    y: PositiveIntList


print(Model2.model_json_schema())
"""
{
    '$defs': {
        'PositiveIntList': {
            'items': {'exclusiveMinimum': 0, 'type': 'integer'},
            'type': 'array',
        }
    },
    'properties': {
        'x': {'$ref': '#/$defs/PositiveIntList'},
        'y': {'$ref': '#/$defs/PositiveIntList'},
    },
    'required': ['x', 'y'],
    'title': 'Model2',
    'type': 'object',
}
"""
```

These named type aliases can also be generic:

```python
from typing import Generic, List, TypeVar

from annotated_types import Gt
from typing_extensions import Annotated, TypeAliasType

from pydantic import BaseModel, ValidationError

T = TypeVar('T')  # or a `bound=SupportGt`

PositiveList = TypeAliasType(
    'PositiveList', List[Annotated[T, Gt(0)]], type_params=(T,)
)


class Model(BaseModel, Generic[T]):
    x: PositiveList[T]


assert Model[int].model_validate_json('{"x": ["1"]}').x == [1]

try:
    Model[int](x=[-1])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model[int]
    x.0
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```

#### Named recursive types

You can also use `TypeAliasType` to create recursive types:

```python
from typing import Any, Dict, List, Union

from pydantic_core import PydanticCustomError
from typing_extensions import Annotated, TypeAliasType

from pydantic import (
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)


def json_custom_error_validator(
    value: Any, handler: ValidatorFunctionWrapHandler, _info: ValidationInfo
) -> Any:
    """Simplify the error message to avoid a gross error stemming
    from exhaustive checking of all union options.
    """
    try:
        return handler(value)
    except ValidationError:
        raise PydanticCustomError(
            'invalid_json',
            'Input is not valid json',
        )


Json = TypeAliasType(
    'Json',
    Annotated[
        Union[Dict[str, 'Json'], List['Json'], str, int, float, bool, None],
        WrapValidator(json_custom_error_validator),
    ],
)


ta = TypeAdapter(Json)

v = ta.validate_python({'x': [1], 'y': {'z': True}})
assert v == {'x': [1], 'y': {'z': True}}

try:
    ta.validate_python({'x': object()})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for function-wrap[json_custom_error_validator()]
      Input is not valid json [type=invalid_json, input_value={'x': <object object at 0x0123456789ab>}, input_type=dict]
    """
```

### Customizing validation with `__get_pydantic_core_schema__` <a name="customizing_validation_with_get_pydantic_core_schema"></a>

To do more extensive customization of how Pydantic handles custom classes, and in particular when you have access to the
class or can subclass it, you can implement a special `__get_pydantic_core_schema__` to tell Pydantic how to generate the
`pydantic-core` schema.

While `pydantic` uses `pydantic-core` internally to handle validation and serialization, it is a new API for Pydantic V2,
thus it is one of the areas most likely to be tweaked in the future and you should try to stick to the built-in
constructs like those provided by `annotated-types`, `pydantic.Field`, or `BeforeValidator` and so on.

You can implement `__get_pydantic_core_schema__` both on a custom type and on metadata intended to be put in `Annotated`.
In both cases the API is middleware-like and similar to that of "wrap" validators: you get a `source_type` (which isn't
necessarily the same as the class, in particular for generics) and a `handler` that you can call with a type to either
call the next metadata in `Annotated` or call into Pydantic's internal schema generation.

The simplest no-op implementation calls the handler with the type you are given, then returns that as the result. You can
also choose to modify the type before calling the handler, modify the core schema returned by the handler, or not call the
handler at all.

#### As a method on a custom type

The following is an example of a type that uses `__get_pydantic_core_schema__` to customize how it gets validated.
This is equivalent to implementing `__get_validators__` in Pydantic V1.

```python
from typing import Any

from pydantic_core import CoreSchema, core_schema

from pydantic import GetCoreSchemaHandler, TypeAdapter


class Username(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


ta = TypeAdapter(Username)
res = ta.validate_python('abc')
assert isinstance(res, Username)
assert res == 'abc'
```

See [JSON Schema](../concepts/json_schema.md) for more details on how to customize JSON schemas for custom types.

#### As an annotation

Often you'll want to parametrize your custom type by more than just generic type parameters (which you can do via the type system and will be discussed later). Or you may not actually care (or want to) make an instance of your subclass; you actually want the original type, just with some extra validation done.

For example, if you were to implement `pydantic.AfterValidator` (see [Adding validation and serialization](#adding-validation-and-serialization)) yourself, you'd do something similar to the following:

```python
from dataclasses import dataclass
from typing import Any, Callable

from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, GetCoreSchemaHandler


@dataclass(frozen=True)  # (1)!
class MyAfterValidator:
    func: Callable[[Any], Any]

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            self.func, handler(source_type)
        )


Username = Annotated[str, MyAfterValidator(str.lower)]


class Model(BaseModel):
    name: Username


assert Model(name='ABC').name == 'abc'  # (2)!
```

1. The `frozen=True` specification makes `MyAfterValidator` hashable. Without this, a union such as `Username | None` will raise an error.
2. Notice that type checkers will not complain about assigning `'ABC'` to `Username` like they did in the previous example because they do not consider `Username` to be a distinct type from `str`.

#### Handling third-party types

Another use case for the pattern in the previous section is to handle third party types.

```python
from typing import Any

from pydantic_core import core_schema
from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue


class ThirdPartyType:
    """
    This is meant to represent a type from a third-party library that wasn't designed with Pydantic
    integration in mind, and so doesn't have a `pydantic_core.CoreSchema` or anything.
    """

    x: int

    def __init__(self):
        self.x = 0


class _ThirdPartyTypePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        We return a pydantic_core.CoreSchema that behaves in the following ways:

        * ints will be parsed as `ThirdPartyType` instances with the int as the x attribute
        * `ThirdPartyType` instances will be parsed as `ThirdPartyType` instances without any changes
        * Nothing else will pass validation
        * Serialization will always return just an int
        """

        def validate_from_int(value: int) -> ThirdPartyType:
            result = ThirdPartyType()
            result.x = value
            return result

        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(validate_from_int),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_int_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(ThirdPartyType),
                    from_int_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.x
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(core_schema.int_schema())


# We now create an `Annotated` wrapper that we'll use as the annotation for fields on `BaseModel`s, etc.
PydanticThirdPartyType = Annotated[
    ThirdPartyType, _ThirdPartyTypePydanticAnnotation
]


# Create a model class that uses this annotation as a field
class Model(BaseModel):
    third_party_type: PydanticThirdPartyType


# Demonstrate that this field is handled correctly, that ints are parsed into `ThirdPartyType`, and that
# these instances are also "dumped" directly into ints as expected.
m_int = Model(third_party_type=1)
assert isinstance(m_int.third_party_type, ThirdPartyType)
assert m_int.third_party_type.x == 1
assert m_int.model_dump() == {'third_party_type': 1}

# Do the same thing where an instance of ThirdPartyType is passed in
instance = ThirdPartyType()
assert instance.x == 0
instance.x = 10

m_instance = Model(third_party_type=instance)
assert isinstance(m_instance.third_party_type, ThirdPartyType)
assert m_instance.third_party_type.x == 10
assert m_instance.model_dump() == {'third_party_type': 10}

# Demonstrate that validation errors are raised as expected for invalid inputs
try:
    Model(third_party_type='a')
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    third_party_type.is-instance[ThirdPartyType]
      Input should be an instance of ThirdPartyType [type=is_instance_of, input_value='a', input_type=str]
    third_party_type.chain[int,function-plain[validate_from_int()]]
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """


assert Model.model_json_schema() == {
    'properties': {
        'third_party_type': {'title': 'Third Party Type', 'type': 'integer'}
    },
    'required': ['third_party_type'],
    'title': 'Model',
    'type': 'object',
}
```

You can use this approach to e.g. define behavior for Pandas or Numpy types.

#### Using `GetPydanticSchema` to reduce boilerplate

??? api "API Documentation"
    [`pydantic.types.GetPydanticSchema`][pydantic.types.GetPydanticSchema]<br>

You may notice that the above examples where we create a marker class require a good amount of boilerplate.
For many simple cases you can greatly minimize this by using `pydantic.GetPydanticSchema`:

```python
from pydantic_core import core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, GetPydanticSchema


class Model(BaseModel):
    y: Annotated[
        str,
        GetPydanticSchema(
            lambda tp, handler: core_schema.no_info_after_validator_function(
                lambda x: x * 2, handler(tp)
            )
        ),
    ]


assert Model(y='ab').y == 'abab'
```

#### Summary

Let's recap:

1. Pydantic provides high level hooks to customize types via `Annotated` like `AfterValidator` and `Field`. Use these when possible.
2. Under the hood these use `pydantic-core` to customize validation, and you can hook into that directly using `GetPydanticSchema` or a marker class with `__get_pydantic_core_schema__`.
3. If you really want a custom type you can implement `__get_pydantic_core_schema__` on the type itself.

### Handling custom generic classes

!!! warning
    This is an advanced technique that you might not need in the beginning. In most of
    the cases you will probably be fine with standard Pydantic models.

You can use
[Generic Classes](https://docs.python.org/3/library/typing.html#typing.Generic) as
field types and perform custom validation based on the "type parameters" (or sub-types)
with `__get_pydantic_core_schema__`.

If the Generic class that you are using as a sub-type has a classmethod
`__get_pydantic_core_schema__`, you don't need to use
[`arbitrary_types_allowed`][pydantic.config.ConfigDict.arbitrary_types_allowed] for it to work.

Because the `source_type` parameter is not the same as the `cls` parameter, you can use `typing.get_args` (or `typing_extensions.get_args`) to extract the generic parameters.
Then you can use the `handler` to generate a schema for them by calling `handler.generate_schema`.
Note that we do not do something like `handler(get_args(source_type)[0])` because we want to generate an unrelated
schema for that generic parameter, not one that is influenced by the current context of `Annotated` metadata and such.
This is less important for custom types, but crucial for annotated metadata that modifies schema building.

```python
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic_core import CoreSchema, core_schema
from typing_extensions import get_args, get_origin

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    ValidationError,
    ValidatorFunctionWrapHandler,
)

ItemType = TypeVar('ItemType')


# This is not a pydantic model, it's an arbitrary generic class
@dataclass
class Owner(Generic[ItemType]):
    name: str
    item: ItemType

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        origin = get_origin(source_type)
        if origin is None:  # used as `x: Owner` without params
            origin = source_type
            item_tp = Any
        else:
            item_tp = get_args(source_type)[0]
        # both calling handler(...) and handler.generate_schema(...)
        # would work, but prefer the latter for conceptual and consistency reasons
        item_schema = handler.generate_schema(item_tp)

        def val_item(
            v: Owner[Any], handler: ValidatorFunctionWrapHandler
        ) -> Owner[Any]:
            v.item = handler(v.item)
            return v

        python_schema = core_schema.chain_schema(
            # `chain_schema` means do the following steps in order:
            [
                # Ensure the value is an instance of Owner
                core_schema.is_instance_schema(cls),
                # Use the item_schema to validate `items`
                core_schema.no_info_wrap_validator_function(
                    val_item, item_schema
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            # for JSON accept an object with name and item keys
            json_schema=core_schema.chain_schema(
                [
                    core_schema.typed_dict_schema(
                        {
                            'name': core_schema.typed_dict_field(
                                core_schema.str_schema()
                            ),
                            'item': core_schema.typed_dict_field(item_schema),
                        }
                    ),
                    # after validating the json data convert it to python
                    core_schema.no_info_before_validator_function(
                        lambda data: Owner(
                            name=data['name'], item=data['item']
                        ),
                        # note that we reuse the same schema here as below
                        python_schema,
                    ),
                ]
            ),
            python_schema=python_schema,
        )


class Car(BaseModel):
    color: str


class House(BaseModel):
    rooms: int


class Model(BaseModel):
    car_owner: Owner[Car]
    home_owner: Owner[House]


model = Model(
    car_owner=Owner(name='John', item=Car(color='black')),
    home_owner=Owner(name='James', item=House(rooms=3)),
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        car_owner=Owner(name='John', item=House(rooms=3)),
        home_owner=Owner(name='James', item=Car(color='black')),
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    wine
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='Kinda good', input_type=str]
    cheese
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='yeah', input_type=str]
    """

# Similarly with JSON
model = Model.model_validate_json(
    '{"car_owner":{"name":"John","item":{"color":"black"}},"home_owner":{"name":"James","item":{"rooms":3}}}'
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    Model.model_validate_json(
        '{"car_owner":{"name":"John","item":{"rooms":3}},"home_owner":{"name":"James","item":{"color":"black"}}}'
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    car_owner.item.color
      Field required [type=missing, input_value={'rooms': 3}, input_type=dict]
    home_owner.item.rooms
      Field required [type=missing, input_value={'color': 'black'}, input_type=dict]
    """
```

#### Generic containers

The same idea can be applied to create generic container types, like a custom `Sequence` type:

```python
from typing import Any, Sequence, TypeVar

from pydantic_core import ValidationError, core_schema
from typing_extensions import get_args

from pydantic import BaseModel, GetCoreSchemaHandler

T = TypeVar('T')


class MySequence(Sequence[T]):
    def __init__(self, v: Sequence[T]):
        self.v = v

    def __getitem__(self, i):
        return self.v[i]

    def __len__(self):
        return len(self.v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        instance_schema = core_schema.is_instance_schema(cls)

        args = get_args(source)
        if args:
            # replace the type and rely on Pydantic to generate the right schema
            # for `Sequence`
            sequence_t_schema = handler.generate_schema(Sequence[args[0]])
        else:
            sequence_t_schema = handler.generate_schema(Sequence)

        non_instance_schema = core_schema.no_info_after_validator_function(
            MySequence, sequence_t_schema
        )
        return core_schema.union_schema([instance_schema, non_instance_schema])


class M(BaseModel):
    model_config = dict(validate_default=True)

    s1: MySequence = [3]


m = M()
print(m)
#> s1=<__main__.MySequence object at 0x0123456789ab>
print(m.s1.v)
#> [3]


class M(BaseModel):
    s1: MySequence[int]


M(s1=[1])
try:
    M(s1=['a'])
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for M
    s1.is-instance[MySequence]
      Input should be an instance of MySequence [type=is_instance_of, input_value=['a'], input_type=list]
    s1.function-after[MySequence(), json-or-python[json=list[int],python=chain[is-instance[Sequence],function-wrap[sequence_validator()]]]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

### Access to field name

!!!note
    This was not possible with Pydantic V2 to V2.3, it was [re-added](https://github.com/pydantic/pydantic/pull/7542) in Pydantic V2.4.

As of Pydantic V2.4, you can access the field name via the `handler.field_name` within `__get_pydantic_core_schema__`
and thereby set the field name which will be available from `info.field_name`.

```python
from typing import Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationInfo


class CustomType:
    """Custom type that stores the field it was used in."""

    def __init__(self, value: int, field_name: str):
        self.value = value
        self.field_name = field_name

    def __repr__(self):
        return f'CustomType<{self.value} {self.field_name!r}>'

    @classmethod
    def validate(cls, value: int, info: ValidationInfo):
        return cls(value, info.field_name)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate, handler(int), field_name=handler.field_name
        )


class MyModel(BaseModel):
    my_field: CustomType


m = MyModel(my_field=1)
print(m.my_field)
#> CustomType<1 'my_field'>
```

You can also access `field_name` from the markers used with `Annotated`, like [`AfterValidator`][pydantic.functional_validators.AfterValidator].

```python
from typing_extensions import Annotated

from pydantic import AfterValidator, BaseModel, ValidationInfo


def my_validators(value: int, info: ValidationInfo):
    return f'<{value} {info.field_name!r}>'


class MyModel(BaseModel):
    my_field: Annotated[int, AfterValidator(my_validators)]


m = MyModel(my_field=1)
print(m.my_field)
#> <1 'my_field'>
```

[PEP 593]: https://peps.python.org/pep-0593/
[PEP 695]: https://peps.python.org/pep-0695/
[typing-extensions]: https://github.com/python/typing_extensions
