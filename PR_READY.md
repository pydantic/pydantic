# PR Ready: Model Injector Feature

## Files Ready for PR

### Core Implementation
- **`pydantic/model_injector.py`** - Main decorator with proper docstrings
- **`pydantic/__init__.py`** - Updated to export `model_inject`

### Documentation
- **`README.md`** - Added feature section with example
- **`docs/examples/model_injector.py`** - Usage examples

### Testing
- **`tests/test_model_injector.py`** - Comprehensive test suite

### Documentation
- **`CHANGES.md`** - Summary of changes

## Features Implemented

1. **Automatic Model Instantiation**: Decorator automatically creates Pydantic model instances from kwargs
2. **Enhanced Error Messages**: Detailed error context with model and field information
3. **Nested Model Support**: Works with complex nested models and type hierarchies
4. **Signature Preservation**: Maintains original function signature and metadata
5. **Type Safety**: Full type hint support and validation
6. **Graceful Error Handling**: Uses `bind_partial` for partial argument matching

## Code Quality

- **Proper Docstrings**: All functions have comprehensive docstrings
- **Type Hints**: Full type annotation support
- **Error Handling**: Comprehensive error handling with detailed messages
- **Testing**: Complete test coverage with pytest
- **Linting**: No linting errors
- **Standards**: Follows Pydantic's coding standards

## Usage Example

```python
from pydantic import BaseModel, Field, model_inject

class UserModel(BaseModel):
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")
    email: str = Field(..., description="User's email")

@model_inject
def create_user(user: UserModel) -> str:
    """Create a user profile from user data."""
    return f"User: {user.name} (Age: {user.age}) - {user.email}"

# Usage
result = create_user(
    name="John Doe",
    age=30,
    email="john@example.com"
)
print(result)  # Output: "User: John Doe (Age: 30) - john@example.com"
```

## Ready for PR

The feature is now ready for a pull request with:
- Clean, production-ready code
- Comprehensive documentation
- Full test coverage
- No breaking changes
- Follows Pydantic's standards

All files are properly organized and ready for review!
