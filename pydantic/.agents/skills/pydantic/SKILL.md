---
name: pydantic
description: Pydantic best practices and conventions. Use when working with Pydantic models, validation, and serialization. Keeps Pydantic code clean and up to date with the latest V2 features and patterns, updated with new versions. Write new code or refactor and update old code.
---

# Pydantic

Official Pydantic skill to write code with best practices, keeping up to date with new versions and features. This skill focuses on **Pydantic V2** patterns and helps avoid outdated V1 code.

## Always Use Pydantic V2 Patterns

Pydantic V2 is the current production release. It offers significant performance improvements, new features, and cleaner APIs. **Always use V2 patterns** and avoid V1 compatibility code.

Do this:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    email: str = Field(
        pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    )
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - V1 patterns
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    email: str = Field(
        regex=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    )  # regex is deprecated, use pattern
```

## Use Modern Type Hints

Use modern Python type hints from `collections.abc` and built-in generics instead of `typing` module imports.

Do this:

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str
    scores: list[int]
    metadata: dict[str, str]
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS — legacy typing generics
from typing import Dict, List

from pydantic import BaseModel


class User(BaseModel):
    name: str
    scores: List[int]
    metadata: Dict[str, str]
```

## Serialization: Use `model_dump()` and `model_dump_json()`

Use V2 serialization methods. The V1 methods are deprecated.

Do this:

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


user = User(id=1, name='Alice')

# Serialize to dict
user_dict = user.model_dump()

# Serialize to JSON string
user_json = user.model_dump_json()

# Serialize with options
user_dict = user.model_dump(include={'id'}, exclude_none=True, by_alias=True)
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - V1 methods are deprecated
user_dict = user.dict()  # Deprecated, use model_dump()
user_json = user.json()  # Deprecated, use model_dump_json()
```

## Validation: Use `model_validate()` and `model_validate_json()`

Use V2 validation class methods instead of deprecated V1 methods.

Do this:

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


# Validate from dict
data = {'id': 1, 'name': 'Alice'}
user = User.model_validate(data)

# Validate from JSON string
json_data = '{"id": 1, "name": "Alice"}'
user = User.model_validate_json(json_data)
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - V1 methods are deprecated
user = User.parse_obj(data)  # Deprecated, use model_validate()
user = User.parse_raw(json_data)  # Deprecated, use model_validate_json()
```

## Use `@field_validator` Instead of `@validator`

The `@validator` decorator is deprecated. Always use `@field_validator` for field-level validation.

Do this:

```python
from pydantic import BaseModel, field_validator


class User(BaseModel):
    name: str
    age: int

    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0:
            raise ValueError('age must be non-negative')
        return v
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - @validator is deprecated
from pydantic import BaseModel, validator


class User(BaseModel):
    name: str
    age: int

    @validator('age')
    def validate_age(cls, v):
        if v < 0:
            raise ValueError('age must be non-negative')
        return v
```

## Use `@model_validator` Instead of `@root_validator`

The `@root_validator` decorator is deprecated. Use `@model_validator` for model-level validation.

Do this:

```python
from pydantic import BaseModel, model_validator


class User(BaseModel):
    password: str
    password_confirm: str

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'User':
        if self.password != self.password_confirm:
            raise ValueError('passwords do not match')
        return self
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - @root_validator is deprecated
from pydantic import BaseModel, root_validator


class User(BaseModel):
    password: str
    password_confirm: str

    @root_validator()
    def check_passwords_match(cls, values):
        if values.get('password') != values.get('password_confirm'):
            raise ValueError('passwords do not match')
        return values
```

## Use `model_config` with `ConfigDict`

The `class Config:` pattern is deprecated. Use `model_config` with `ConfigDict`.

Do this:

```python
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )

    name: str
    email: str
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - class Config is deprecated
from pydantic import BaseModel


class User(BaseModel):
    name: str
    email: str

    class Config:
        anystr_strip_whitespace = True
        validate_assignment = True
        extra = 'forbid'
```

## Use `TypeAdapter` for Non-Model Types

For validating, serializing, or generating JSON schemas for arbitrary types (not just `BaseModel` subclasses), use `TypeAdapter`.

Do this:

```python
from pydantic import TypeAdapter

adapter = TypeAdapter(list[int])
data = adapter.validate_python(['1', '2', '3'])  # [1, 2, 3]
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - parse_obj_as is deprecated
from pydantic import parse_obj_as  # Deprecated

data = parse_obj_as(list[int], ['1', '2', '3'])
```

## Use `RootModel` for Custom Root Types

For models that should validate a single type (like a list or dict), use `RootModel`.

Do this:

```python
from pydantic import RootModel

# Type alias
Tags = RootModel[list[str]]


# Or subclass
class TagsModel(RootModel[list[str]]):
    pass
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - __root__ is removed in V2
from pydantic import BaseModel


class Tags(BaseModel):
    __root__: list[str]  # Removed in V2
```

## Generic Models

Generic models no longer require `GenericModel`. Simply inherit from `BaseModel` and `typing.Generic`.

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class Container(BaseModel, Generic[T]):
    item: T


# Usage
int_container = Container[int](item=42)
str_container = Container[str]
```

## Settings Management

`BaseSettings` has been moved to the `pydantic-settings` package. Install it separately.

Do this:

```python {test="skip"}
# pip install pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    # Example defaults for illustration; in real apps omit defaults and load from the environment
    database_url: str = 'postgres://localhost/db'
    debug: bool = False
    api_key: str = 'dev-placeholder'


settings = Settings()
```

## Use `Field()` for Constraints and Metadata

Use `Field()` for adding constraints, defaults, and metadata to model fields.

Do this:

```python
from typing import Annotated

from pydantic import BaseModel, Field


class Product(BaseModel):
    name: Annotated[
        str, Field(min_length=1, max_length=100, description='Product name')
    ]
    price: Annotated[float, Field(gt=0, le=1000000, description='Price in USD')]
    quantity: Annotated[int, Field(ge=0, default=0)]
    sku: Annotated[str | None, Field(default=None, pattern=r'^[A-Z]{3}-\d{4}$')]
```

## Custom Types with `__get_pydantic_core_schema__`

For custom types, implement `__get_pydantic_core_schema__`.

Do this:

```python
from typing import Any

from pydantic_core import core_schema

from pydantic import GetCoreSchemaHandler


class PhoneNumber(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.str_schema(pattern=r'^\+?[1-9]\d{1,14}$')
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - V1 custom type methods are removed
class PhoneNumber(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
```

## Accessing Model Fields

Use `model_fields` instead of `fields`.

Do this:

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = 'Unknown'
    email: str


user = User(id=1, email='alice@example.com')

# Get field definitions
print(User.model_fields)
"""
{
    'id': FieldInfo(annotation=int, required=True),
    'name': FieldInfo(annotation=str, required=False, default='Unknown'),
    'email': FieldInfo(annotation=str, required=True),
}
"""
# Returns: {'id': FieldInfo(...), 'name': FieldInfo(...), 'email': FieldInfo(...)}

# Check if field is required
print(User.model_fields['name'].is_required())
#> False
# Returns: False
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - V1 attributes are removed/deprecated
print(User.__fields__)  # Removed, use model_fields
```

## Model Construction

Use `model_construct()` for creating models without validation when you trust the data.

Do this:

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


# Fast construction without validation (use with caution)
user = User.model_construct(id=1, name='Alice')
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - construct() is deprecated
user = User.construct(id=1, name='Alice')  # Deprecated
```

## Dataclasses

Pydantic supports standard library dataclasses with validation.

Do this:

```python
from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass


@dataclass
class InventoryItem:
    name: str
    unit_price: float
    quantity_on_hand: int = 0


# Validate
item = InventoryItem(name='Widget', unit_price=3.50, quantity_on_hand=10)

# Use TypeAdapter for schema and validation
adapter = TypeAdapter(InventoryItem)
schema = adapter.json_schema()
```

## Required, Optional, and Nullable Fields

Pydantic V2 follows `dataclass`-like behavior for field requirements.

Do this:

```python
from pydantic import BaseModel


class Example(BaseModel):
    # Required, cannot be None
    field1: str

    # Required, can be None (Optional does NOT provide a default!)
    field2: str | None

    # Not required, defaults to None
    field3: str | None = None

    # Not required, has default value
    field4: str = 'default'

    # Not required, can be None, has default
    field5: str | None = 'default'
```

## Do Not Use Ellipsis for Required Fields

Do not use `...` (Ellipsis) to mark fields as required. Simply omit the default value.

Do this:

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str  # Required - no default
    age: int  # Required - no default
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - Ellipsis is unnecessary
from pydantic import BaseModel


class User(BaseModel):
    name: str = ...  # Unnecessary
    age: int = ...  # Unnecessary
```

## ValidationError Handling

Use `ValidationError` for catching and handling validation errors.

Do this:

```python
from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str


try:
    user = User(id='not an int', name='Alice')
except ValidationError as e:
    # Access structured error information
    for error in e.errors():
        print(f"Field: {error['loc']}, Error: {error['msg']}")
        """
        Field: ('id',), Error: Input should be a valid integer, unable to parse string as an integer
        """

    # Or get as JSON
    print(e.json())
    """
    [{"type":"int_parsing","loc":["id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"not an int","url":"https://errors.pydantic.dev/2/v/int_parsing"}]
    """
```

## Model Rebuilding

Use `model_rebuild()` to rebuild models with forward references or after modifications.

Do this:

```python
from pydantic import BaseModel


class Foo(BaseModel):
    bar: 'Bar'


class Bar(BaseModel):
    value: int


# Rebuild to resolve forward references
Foo.model_rebuild()
```

Instead of this:

```python {test="skip" lint="skip"}
# DO NOT DO THIS - update_forward_refs() is deprecated
Foo.update_forward_refs()  # Deprecated
```

## Performance Best Practices

1. **Use `model_validate()` over manual instantiation** when parsing unknown data
2. **Use `model_construct()` when you trust the data** for better performance
3. **Avoid `@model_validator(mode='wrap')`** unless necessary, as it has overhead
4. **Use `defer_build=True`** in `ConfigDict` if you have many models that might not be used
5. **Consider `TypeAdapter`** for simple type validation instead of full models
