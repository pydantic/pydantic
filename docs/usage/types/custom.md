

You can also define your own custom data types. There are several ways to achieve it.

### Classes with `____get_pydantic_core_schema____`


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
    'type': 'object',
    'properties': {
        'post_code': {
            'type': 'string',
            'pattern': '^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
            'examples': ['SP11 9DG', 'W1J 7BU'],
            'title': 'Post Code',
        }
    },
    'required': ['post_code'],
    'title': 'Model',
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

See [schema](../schema.md) for more details on how the model's schema is generated.

### Arbitrary Types Allowed

You can allow arbitrary types using the `arbitrary_types_allowed` config in the
[Model Config](../model_config.md).

```py
from pydantic import BaseModel, ValidationError


# This is not a pydantic model, it's an arbitrary class
class Pet:
    def __init__(self, name: str):
        self.name = name


class Model(BaseModel):
    model_config = dict(arbitrary_types_allowed=True)
    pet: Pet
    owner: str


pet = Pet(name='Hedwig')
# A simple check of instance type is used to validate the data
model = Model(owner='Harry', pet=pet)
print(model)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model.pet.name)
#> Hedwig
print(type(model.pet))
#> <class '__main__.Pet'>
try:
    # If the value is not an instance of the type, it's invalid
    Model(owner='Harry', pet='Hedwig')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet
      Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
    """
# Nothing in the instance of the arbitrary type is checked
# Here name probably should have been a str, but it's not validated
pet2 = Pet(name=42)
model2 = Model(owner='Harry', pet=pet2)
print(model2)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model2.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model2.pet.name)
#> 42
print(type(model2.pet))
#> <class '__main__.Pet'>
```

### Generic Classes as Types

!!! warning
    This is an advanced technique that you might not need in the beginning. In most of
    the cases you will probably be fine with standard *pydantic* models.

You can use
[Generic Classes](https://docs.python.org/3/library/typing.html#typing.Generic) as
field types and perform custom validation based on the "type parameters" (or sub-types)
with `__get_validators__`.

If the Generic class that you are using as a sub-type has a classmethod
`__get_validators__` you don't need to use `arbitrary_types_allowed` for it to work.

Because you can declare validators that receive the current `field`, you can extract
the `sub_fields` (from the generic class type parameters) and validate data with them.

```py test="xfail - what do we do with generic custom types"
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField

AgedType = TypeVar('AgedType')
QualityType = TypeVar('QualityType')


# This is not a pydantic model, it's an arbitrary generic class
class TastingModel(Generic[AgedType, QualityType]):
    def __init__(self, name: str, aged: AgedType, quality: QualityType):
        self.name = name
        self.aged = aged
        self.quality = quality

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def validate(cls, v, field: ModelField):
        if not isinstance(v, cls):
            # The value is not even a TastingModel
            raise TypeError('Invalid value')
        if not field.sub_fields:
            # Generic parameters were not provided so we don't try to validate
            # them and just return the value as is
            return v
        aged_f = field.sub_fields[0]
        quality_f = field.sub_fields[1]
        errors = []
        # Here we don't need the validated value, but we want the errors
        valid_value, error = aged_f.validate(v.aged, {}, loc='aged')
        if error:
            errors.append(error)
        # Here we don't need the validated value, but we want the errors
        valid_value, error = quality_f.validate(v.quality, {}, loc='quality')
        if error:
            errors.append(error)
        if errors:
            raise ValidationError.from_exception_data(errors, cls)
        # Validation passed without errors, return the same instance received
        return v


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
print(model.wine.aged)
print(model.wine.quality)
print(model.cheese.aged)
print(model.cheese.quality)
print(model.thing.aged)
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
```
