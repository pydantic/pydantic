# Changes for Model Injector Feature

## Summary
Added a new `model_inject` decorator that automatically instantiates Pydantic models from function keyword arguments, similar to FastAPI's behavior.

## Files Added/Modified

### New Files
- `pydantic/model_injector.py` - Main decorator implementation
- `tests/test_model_injector.py` - Test suite for the decorator
- `docs/examples/model_injector.py` - Usage examples

### Modified Files
- `pydantic/__init__.py` - Added `model_inject` to exports
- `README.md` - Added feature documentation with example

## Features
- Automatic model instantiation from function kwargs
- **Positional arguments support** - Models can be passed as positional arguments
- Support for multiple models and nested models
- Enhanced error messages with model and field context
- Preserves original function signature and metadata
- Graceful handling of partial argument matches using `bind_partial`

## Usage
```python
from pydantic import BaseModel, Field, model_inject

class UserModel(BaseModel):
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")

@model_inject
def create_user(user: UserModel) -> str:
    return f"User: {user.name} (Age: {user.age})"

# Usage - Keyword arguments
result = create_user(name="John Doe", age=30)

# Usage - Positional arguments
result = create_user({"name": "Jane Doe", "age": 25})
result = create_user("Alice Johnson")  # Uses first field
```

## Testing
- Comprehensive test suite covering basic functionality, error handling, and edge cases
- All tests pass with existing Pydantic test infrastructure
- No breaking changes to existing functionality
