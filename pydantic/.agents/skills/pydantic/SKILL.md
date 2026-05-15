---
name: pydantic
description: Pydantic best practices and conventions. Use when working with Pydantic models, validation, and serialization. Keeps Pydantic code clean and up to date with the latest V2 features and patterns, updated with new versions. Write new code or refactor and update old code.
---

# Pydantic

Official Pydantic skill to write code with best practices, keeping up to date with new versions and features. This skill focuses on **Pydantic V2** patterns and helps avoid outdated V1 code.

## Always Use Pydantic V2 Patterns

[](#always-use-pydantic-v2-patterns)

Pydantic V2 is the current production release. It offers significant performance improvements, new features, and cleaner APIs. **Always use V2 patterns** and avoid V1 compatibility code.

Do this:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    email: str = Field(pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
```

Instead of this:

```python
# DO NOT DO THIS - V1 patterns
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    email: str = Field(regex=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')  # regex is deprecated, use pattern
```

## Use `Annotated` for Field Metadata

[](#use-annotated-for-field-metadata)

Always prefer `typing.Annotated` for adding field metadata and constraints. It keeps type annotations clean and compatible with type checkers.

Do this:

```python
from typing import Annotated

from pydantic import BaseModel, Field

class Item(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    price: Annotated[float, Field(gt=0)]
    tags: Annotated[list[str], Field(default_factory=list)]
```

Instead of this:

```python
# DO NOT DO THIS
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    tags: list[str] = Field(default_factory=list)
```

## Use Modern Type Hints

[](#use-modern-type-hints)

Use modern Python type hints from `collections.abc` and built-in generics instead of `typing` module imports.

Do this:

```python
from collections.abc import Sequence, Mapping

from pydantic import BaseModel

class User(BaseModel):
    name: str
    scores: list[int]
    metadata: dict[str, str]
    items: Sequence[str]
    mapping: Mapping[str, int]
```

Instead of this:

```python
# DO NOT DO THIS
from typing import List, Dict, Sequence, Mapping

from pydantic import BaseModel

class User(BaseModel):
    name: str
    scores: List[int]  # Use list[int] instead
    metadata: Dict[str, str]  # Use dict[str, str] instead
    items: Sequence[str]
    mapping: Mapping[str, int]
```

## Serialization: Use `model_dump()` and `model_dump_json()`

[](#serialization-use-model_dump-and-model_dump_json)

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

```python
# DO NOT DO THIS - V1 methods are deprecated
user_dict = user.dict()  # Deprecated, use model_dump()
user_json = user.json()  # Deprecated, use model_dump_json()
```

## Validation: Use `model_validate()` and `model_validate_json()`

[](#validation-use-model_validate-and-model_validate_json)

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

```python
# DO NOT DO THIS - V1 methods are deprecated
user = User.parse_obj(data)  # Deprecated, use model_validate()
user = User.parse_raw(json_data)  # Deprecated, use model_validate_json()
```

## Use `@field_validator` Instead of `@validator`

[](#use-field_validator-instead-of-validator)

The `@validator` decorator is deprecated. Always use `@field_validator` for field-level validation.

Do this:

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class User(BaseModel):
    name: str
    age: int

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('name must not be empty')
        return v.strip()

    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int, info: ValidationInfo) -> int:
        if v < 0:
            raise ValueError('age must be non-negative')
        return v
```

Instead of this:

```python
# DO NOT DO THIS - @validator is deprecated
from pydantic import BaseModel, validator

class User(BaseModel):
    name: str
    age: int

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('name must not be empty')
        return v.strip()

    @validator('age')
    def validate_age(cls, v, values, **kwargs):
        if v < 0:
            raise ValueError('age must be non-negative')
        return v
```

### Field Validator Key Differences

- Must use `@classmethod`
- Signature is cleaner: no `values`, `config`, or `field` parameters
- Use `ValidationInfo` for accessing context if needed
- No `each_item` parameter; use `Annotated` for container item validation

## Use `@model_validator` Instead of `@root_validator`

[](#use-model_validator-instead-of-root_validator)

The `@root_validator` decorator is deprecated. Use `@model_validator` for model-level validation.

Do this:

```python
from typing import Any

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

Or with `mode='before'` for dict-based validation:

```python
from typing import Any

from pydantic import BaseModel, model_validator

class User(BaseModel):
    first_name: str
    last_name: str
    full_name: str

    @model_validator(mode='before')
    @classmethod
    def set_full_name(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'full_name' not in data:
            data['full_name'] = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        return data
```

Instead of this:

```python
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

[](#use-model_config-with-configdict)

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

```python
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

### Common Config Migrations

| V1 (Deprecated) | V2 (Use This) |
|----------------|---------------|
| `allow_population_by_field_name` | `populate_by_name` |
| `anystr_lower` | `str_to_lower` |
| `anystr_strip_whitespace` | `str_strip_whitespace` |
| `anystr_upper` | `str_to_upper` |
| `orm_mode` | `from_attributes` |
| `schema_extra` | `json_schema_extra` |
| `validate_all` | `validate_default` |
| `max_anystr_length` | `str_max_length` |
| `min_anystr_length` | `str_min_length` |
| `underscore_attrs_are_private` | Removed (always True) |

## Use `TypeAdapter` for Non-Model Types

[](#use-typeadapter-for-non-model-types)

For validating, serializing, or generating JSON schemas for arbitrary types (not just `BaseModel` subclasses), use `TypeAdapter`.

Do this:

```python
from pydantic import TypeAdapter

# Create adapter for any type
adapter = TypeAdapter(list[int])

# Validate data
data = adapter.validate_python(['1', '2', '3'])
# Returns: [1, 2, 3]

# Validate from JSON
json_data = '[1, 2, 3]'
data = adapter.validate_json(json_data)

# Generate JSON schema
schema = adapter.json_schema()
```

Instead of this:

```python
# DO NOT DO THIS - parse_obj_as is deprecated
from pydantic import parse_obj_as  # Deprecated

data = parse_obj_as(list[int], ['1', '2', '3'])
```

## Use `RootModel` for Custom Root Types

[](#use-rootmodel-for-custom-root-types)

For models that should validate a single type (like a list or dict), use `RootModel`.

Do this:

```python
from pydantic import RootModel

class Tags(RootModel[list[str]]):
    pass

# Or with constraints
from typing import Annotated
from pydantic import Field

class Tags(RootModel[list[Annotated[str, Field(min_length=1)]]]):
    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
```

Instead of this:

```python
# DO NOT DO THIS - __root__ is removed in V2
from pydantic import BaseModel

class Tags(BaseModel):
    __root__: list[str]  # Removed in V2
```

## Generic Models

[](#generic-models)

Generic models no longer require `GenericModel`. Simply inherit from `BaseModel` and `typing.Generic`.

Do this:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')

class Container(BaseModel, Generic[T]):
    item: T

# Usage
int_container = Container[int](item=42)
str_container = Container[str](item='hello')
```

Instead of this:

```python
# DO NOT DO THIS - GenericModel is removed in V2
from pydantic.generics import GenericModel  # Removed in V2
```

## Settings Management

[](#settings-management)

`BaseSettings` has been moved to the `pydantic-settings` package. Install it separately.

Do this:

```python
# pip install pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    api_key: str

    class Config:
        env_file = '.env'

settings = Settings()
```

Instead of this:

```python
# DO NOT DO THIS - BaseSettings moved to pydantic-settings
from pydantic import BaseSettings  # Moved in V2
```

## Use `Field()` for Constraints and Metadata

[](#use-field-for-constraints-and-metadata)

Use `Field()` for adding constraints, defaults, and metadata to model fields.

Do this:

```python
from typing import Annotated

from pydantic import BaseModel, Field

class Product(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100, description='Product name')]
    price: Annotated[float, Field(gt=0, le=1000000, description='Price in USD')]
    quantity: Annotated[int, Field(ge=0, default=0)]
    sku: Annotated[str | None, Field(default=None, pattern=r'^[A-Z]{3}-\d{4}$')]
```

## Custom Types with `__get_pydantic_core_schema__`

[](#custom-types-with-get_pydantic_core_schema)

For custom types, implement `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__`.

Do this:

```python
from typing import Any

from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue

class PhoneNumber(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.str_schema(pattern=r'^\+?[1-9]\d{1,14}$')

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema.update(type='string', format='phone')
        return json_schema
```

Instead of this:

```python
# DO NOT DO THIS - V1 custom type methods are removed
class PhoneNumber(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        # ... validation logic
        return v

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(format='phone')
```

## Accessing Model Fields

[](#accessing-model-fields)

Use `model_fields` and `model_fields_set` instead of deprecated V1 attributes.

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
# Returns: {'id': FieldInfo(...), 'name': FieldInfo(...), 'email': FieldInfo(...)}

# Get fields that were explicitly set
print(user.model_fields_set)
# Returns: {'id', 'email'}

# Check if field is required
print(User.model_fields['name'].is_required())
# Returns: False
```

Instead of this:

```python
# DO NOT DO THIS - V1 attributes are removed/deprecated
print(User.__fields__)  # Removed, use model_fields
print(user.__fields_set__)  # Deprecated, use model_fields_set
```

## Model Construction

[](#model-construction)

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

```python
# DO NOT DO THIS - construct() is deprecated
user = User.construct(id=1, name='Alice')  # Deprecated
```

## Dataclasses

[](#dataclasses)

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

[](#required-optional-and-nullable-fields)

Pydantic V2 follows `dataclass`-like behavior for field requirements.

Do this:

```python
from typing import Optional

from pydantic import BaseModel

class Example(BaseModel):
    # Required, cannot be None
    field1: str

    # Required, can be None (Optional does NOT provide a default!)
    field2: Optional[str]

    # Not required, defaults to None
    field3: Optional[str] = None

    # Not required, has default value
    field4: str = 'default'

    # Not required, can be None, has default
    field5: Optional[str] = 'default'
```

## Do Not Use Ellipsis for Required Fields

[](#do-not-use-ellipsis-for-required-fields)

Do not use `...` (Ellipsis) to mark fields as required. Simply omit the default value.

Do this:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str  # Required - no default
    age: int   # Required - no default
```

Instead of this:

```python
# DO NOT DO THIS - Ellipsis is unnecessary
class User(BaseModel):
    name: str = ...  # Unnecessary
    age: int = ...   # Unnecessary
```

## ValidationError Handling

[](#validationerror-handling)

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

    # Or get as JSON
    print(e.json())
```

## Model Rebuilding

[](#model-rebuilding)

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

```python
# DO NOT DO THIS - update_forward_refs() is deprecated
Foo.update_forward_refs()  # Deprecated
```

## Performance Best Practices

[](#performance-best-practices)

1. **Use `model_validate()` over manual instantiation** when parsing unknown data
2. **Use `model_construct()` when you trust the data** for better performance
3. **Avoid `@model_validator(mode='wrap')`** unless necessary, as it has overhead
4. **Use `defer_build=True`** in `ConfigDict` if you have many models that might not be used
5. **Consider `TypeAdapter`** for simple type validation instead of full models
