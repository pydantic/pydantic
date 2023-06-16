

You can also define your own custom data types. There are several ways to achieve it.

### Composing types via `Annotated`

[PEP 593] introduced `Annotated` as a way to attach runtime metadata to types without changing how type checkers interpret them.
Pydantic takes advantage of this to allow you to create types that are identical to the original type as far as type checkers are concerned, but add validation, serialize differently, etc.
For example, to create a type representing a positive int:

```py
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

Note that you can also use constraints from [`annotated-types`] to make this Pydantic-agnostic:

```py
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

You can add or override validation, serialization, and json schemas to an arbitrary type using the markers that Pydantic exports:

```py
from typing_extensions import Annotated

from pydantic import AfterValidator, PlainSerializer, TypeAdapter, WithJsonSchema


class MyType:
    def __init__(self, value: str) -> None:
        self.value = value


TrucatedFloat = Annotated[
    float,
    AfterValidator(lambda x: round(x, 1)),
    PlainSerializer(lambda x: f'{x:.1e}', return_type=str),
    WithJsonSchema({'type': 'string'}, mode='serialization'),
]


ta = TypeAdapter(TrucatedFloat)

input = 1.02345
assert input != 1.0

assert ta.validate_python(input) == 1.0

assert ta.dump_json(input) == b'"1.0e+00"'

assert ta.json_schema(mode='validation') == {'type': 'number'}
assert ta.json_schema(mode='serialization') == {'type': 'string'}
```

#### Generics

You can use type variables within `Annotated` to make re-usable modifications to types:

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
      List should have at most 10 items after validation, not 11 [type=too_long, input_value=[1, 1, 1, 1, 1, 1, 1, 1, ... 1, 1, 1, 1, 1, 1, 1, 1], input_type=list]
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

```py
from typing import List, TypeVar

from annotated_types import Gt
from typing_extensions import Annotated, TypeAliasType

from pydantic import BaseModel

T = TypeVar('T')  # or a `bound=SupportGt`

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

```py
from typing import Generic, List, TypeVar

from annotated_types import Gt
from typing_extensions import Annotated, TypeAliasType

from pydantic import BaseModel, ValidationError

T = TypeVar('T')  # or a bound=SupportGt

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

```py
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

### Classes with `__get_pydantic_core_schema__`

```py
import re
from typing import Any

from pydantic_core import PydanticCustomError, core_schema
from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue

# https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom#Validation
post_code_regex = re.compile(
    r'(?:'
    r'([A-Z]{1,2}[0-9][A-Z0-9]?|ASCN|STHL|TDCU|BBND|[BFS]IQQ|PCRN|TKCA) ?'
    r'([0-9][A-Z]{2})|'
    r'(BFPO) ?([0-9]{1,4})|'
    r'(KY[0-9]|MSR|VG|AI)[ -]?[0-9]{4}|'
    r'([A-Z]{2}) ?([0-9]{2})|'
    r'(GE) ?(CX)|'
    r'(GIR) ?(0A{2})|'
    r'(SAN) ?(TA1)'
    r')'
)


class PostCodeAnnotation:
    """
    Partial UK postcode validation. Note: this is just an example, and is not
    intended for use in production; in particular this does NOT guarantee
    a postcode exists, just that it has a valid format.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(schema)
        json_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern='^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
            # some example postcodes
            examples=['SP11 9DG', 'W1J 7BU'],
        )
        return json_schema

    @classmethod
    def validate(cls, v: str):
        m = post_code_regex.fullmatch(v.upper())
        if m:
            return f'{m.group(1)} {m.group(2)}'
        else:
            raise PydanticCustomError('postcode', 'invalid postcode format')


class Model(BaseModel):
    post_code: Annotated[str, PostCodeAnnotation]


model = Model(post_code='sw8 5el')
print(model)
#> post_code='SW8 5EL'
print(model.post_code)
#> SW8 5EL
print(Model.model_json_schema())
"""
{
    'properties': {
        'post_code': {
            'examples': ['SP11 9DG', 'W1J 7BU'],
            'pattern': '^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
            'title': 'Post Code',
            'type': 'string',
        }
    },
    'required': ['post_code'],
    'title': 'Model',
    'type': 'object',
}
"""
try:
    Model(post_code='invalid')
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'postcode',
            'loc': ('post_code',),
            'msg': 'invalid postcode format',
            'input': 'invalid',
        }
    ]
    """
```

Similar validation could be achieved using [`constr(regex=...)`](#constrained-types) except the value won't be
formatted with a space, the schema would just include the full pattern and the returned value would be a vanilla string.

See [schema](../json_schema.md) for more details on how the model's schema is generated.

### Generic Classes as Types

!!! warning
    This is an advanced technique that you might not need in the beginning. In most of
    the cases you will probably be fine with standard Pydantic models.

You can use
[Generic Classes](https://docs.python.org/3/library/typing.html#typing.Generic) as
field types and perform custom validation based on the "type parameters" (or sub-types)
with `__get_validators__`.

If the Generic class that you are using as a sub-type has a classmethod
`__get_validators__` you don't need to use [`arbitrary_types_allowed`](../model_config.md#arbitrary-types-allowed) for it to work.

Because you can declare validators that receive the current `field`, you can extract
the `sub_fields` (from the generic class type parameters) and validate data with them.

```py
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic_core import CoreSchema, core_schema
from typing_extensions import get_args, get_origin

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationError

AgedType = TypeVar('AgedType')
QualityType = TypeVar('QualityType')


# This is not a pydantic model, it's an arbitrary generic class
@dataclass
class TastingModel(Generic[AgedType, QualityType]):
    name: str
    aged: AgedType
    quality: QualityType

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        origin = get_origin(source_type)
        if origin is None:  # used as `x: TastingModel` without params
            origin = source_type
            age_tp = quality_tp = Any
        else:
            age_tp, quality_tp = get_args(source_type)
        aged_schema = handler(age_tp)
        quality_schema = handler(quality_tp)

        def val_aged(
            v: TastingModel[Any, Any], handler: core_schema.ValidatorFunctionWrapHandler
        ) -> Any:
            v.aged = handler(v.aged)
            return v

        def val_quality(
            v: TastingModel[Any, Any], handler: core_schema.ValidatorFunctionWrapHandler
        ) -> Any:
            v.quality = handler(v.quality)
            return v

        return core_schema.chain_schema(
            # `chain_schema` means do the following steps in order:
            [
                # Ensure the value is an instance of TastingModel
                core_schema.is_instance_schema(cls),
                # Use the aged_schema to validate the `aged` field of generic type `AgedType`
                core_schema.no_info_wrap_validator_function(val_aged, aged_schema),
                # Use the quality_schema to validate the `quality` field of generic type `QualityType`
                core_schema.no_info_wrap_validator_function(
                    val_quality, quality_schema
                ),
            ]
        )


class Model(BaseModel):
    # for wine, "aged" is an int with years, "quality" is a float
    wine: TastingModel[int, float]
    # for cheese, "aged" is a bool, "quality" is a str
    cheese: TastingModel[bool, str]
    # for thing, "aged" is a Any, "quality" is Any
    thing: TastingModel


model = Model(
    # This wine was aged for 20 years and has a quality of 85.6
    wine=TastingModel(name='Cabernet Sauvignon', aged=20, quality=85.6),
    # This cheese is aged (is mature) and has "Good" quality
    cheese=TastingModel(name='Gouda', aged=True, quality='Good'),
    # This Python thing has aged "Not much" and has a quality "Awesome"
    thing=TastingModel(name='Python', aged='Not much', quality='Awesome'),
)
print(model)
"""
wine=TastingModel(name='Cabernet Sauvignon', aged=20, quality=85.6) cheese=TastingModel(name='Gouda', aged=True, quality='Good') thing=TastingModel(name='Python', aged='Not much', quality='Awesome')
"""
print(model.wine.aged)
#> 20
print(model.wine.quality)
#> 85.6
print(model.cheese.aged)
#> True
print(model.cheese.quality)
#> Good
print(model.thing.aged)
#> Not much
try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        # For wine, aged should be an int with the years, and quality a float
        wine=TastingModel(name='Merlot', aged=True, quality='Kinda good'),
        # For cheese, aged should be a bool, and quality a str
        cheese=TastingModel(name='Gouda', aged='yeah', quality=5),
        # For thing, no type parameters are declared, and we skipped validation
        # in those cases in the Assessment.validate() function
        thing=TastingModel(name='Python', aged='Not much', quality='Awesome'),
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    wine
      Input should be a valid number, unable to parse string as an number [type=float_parsing, input_value='Kinda good', input_type=str]
    cheese
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='yeah', input_type=str]
    """
```

[PEP 593]: https://peps.python.org/pep-0593/
[PEP 695]: https://peps.python.org/pep-0695/
[typing-extensions]: https://github.com/python/typing_extensions
