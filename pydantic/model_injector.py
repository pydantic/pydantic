"""Model injector decorator for automatic Pydantic model instantiation from function arguments."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, Type, TypeVar, get_type_hints, get_origin, get_args, Union
from pydantic import BaseModel, ValidationError

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])


def model_inject(func: F) -> F:
    """Automatically instantiate Pydantic models from function keyword arguments.
    
    This decorator inspects the function signature to identify parameters annotated with
    Pydantic models. When the decorated function is called, it automatically extracts
    matching keyword arguments and instantiates the corresponding Pydantic models.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function with automatic model instantiation.
        
    Raises:
        ValidationError: If required model fields are missing or invalid data is provided.
        TypeError: If there are issues with argument binding or model instantiation.
        
    Example:
        ```python
        from pydantic import BaseModel, Field, model_inject
        
        class UserModel(BaseModel):
            name: str = Field(..., description="User's name")
            age: int = Field(..., ge=0, le=150, description="User's age")
        
        @model_inject
        def create_user(user: UserModel) -> str:
            return f"User: {user.name} (Age: {user.age})"
        
        # Usage
        result = create_user(name="John Doe", age=30)
        ```
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the function signature
        sig = inspect.signature(func)
        
        # Get type hints for the function
        type_hints = get_type_hints(func)
        
        # Create a mapping of parameter names to their types
        param_types = {}
        for param_name, param in sig.parameters.items():
            if param_name in type_hints:
                param_types[param_name] = type_hints[param_name]
        
        # Identify parameters that are Pydantic models
        model_params = {}
        for param_name, param_type in param_types.items():
            if _is_pydantic_model(param_type):
                model_params[param_name] = param_type
        
        if not model_params:
            # No Pydantic models found, call function normally
            return func(*args, **kwargs)
        
        # Use bind_partial to handle partial matches gracefully
        # We need to be more careful about which kwargs to pass to bind_partial
        # Only pass kwargs that are not model fields
        model_kwargs = set()
        for model_class in model_params.values():
            if hasattr(model_class, 'model_fields'):
                model_kwargs.update(model_class.model_fields.keys())
            else:
                # Fallback for older Pydantic versions
                model_kwargs.update(getattr(model_class, '__fields__', {}).keys())
        
        # Separate model kwargs from regular kwargs
        regular_kwargs = {k: v for k, v in kwargs.items() if k not in model_kwargs}
        
        # Handle positional arguments for model parameters
        # If we have positional args and model parameters, we need to handle them specially
        if args and model_params:
            # For model parameters, we'll handle positional args separately
            # Only bind non-model parameters to the signature
            non_model_params = {name: param for name, param in sig.parameters.items() 
                              if name not in model_params}
            
            if non_model_params:
                # Only bind if there are non-model parameters
                try:
                    bound_args = sig.bind_partial(*args, **regular_kwargs)
                except TypeError as e:
                    raise TypeError(f"Error binding arguments for function '{func.__name__}': {e}")
            else:
                # No non-model parameters, create empty bound args
                bound_args = sig.bind_partial()
        else:
            try:
                bound_args = sig.bind_partial(*args, **regular_kwargs)
            except TypeError as e:
                raise TypeError(f"Error binding arguments for function '{func.__name__}': {e}")
        
        # Create model instances for each model parameter
        model_instances = {}
        remaining_kwargs = dict(kwargs)
        
        # Handle positional arguments for model parameters
        model_param_names = list(model_params.keys())
        model_param_values = list(bound_args.arguments.values())
        
        for i, (param_name, model_class) in enumerate(model_params.items()):
            # Start with kwargs that match the model fields
            model_kwargs = _extract_model_kwargs(model_class, remaining_kwargs)
            
            # Check if we have a positional argument for this model parameter
            if i < len(args) and param_name not in bound_args.arguments:
                # Use the positional argument as the model data
                model_data = args[i]
                if isinstance(model_data, dict):
                    # If it's a dict, merge it with existing kwargs
                    model_kwargs.update(model_data)
                else:
                    # If it's not a dict, we need to handle multiple positional args
                    # Get all remaining positional args for this model
                    remaining_args = args[i:]
                    
                    # Get field names for this model
                    if hasattr(model_class, 'model_fields'):
                        field_names = list(model_class.model_fields.keys())
                    else:
                        field_names = list(getattr(model_class, '__fields__', {}).keys())
                    
                    # Create kwargs from positional args and field names
                    # Only use positional args for fields that don't already have values from kwargs
                    for j, field_name in enumerate(field_names):
                        if j < len(remaining_args):
                            # Keyword arguments take precedence over positional ones
                            if field_name not in model_kwargs:
                                model_kwargs[field_name] = remaining_args[j]
                        elif j >= len(remaining_args):
                            # If we don't have enough args, we'll let Pydantic handle the missing fields
                            break
            
            try:
                
                # Create the model instance
                model_instance = model_class(**model_kwargs)
                model_instances[param_name] = model_instance
                
                # Remove used kwargs to avoid conflicts
                for key in model_kwargs:
                    remaining_kwargs.pop(key, None)
                    
            except ValidationError as e:
                # Enhanced error message with model and field context
                error_details = []
                for error in e.errors():
                    field_path = " -> ".join(str(loc) for loc in error['loc'])
                    error_details.append(f"  {field_path}: {error['msg']}")
                
                error_msg = (
                    f"Validation failed for model '{model_class.__name__}' in parameter '{param_name}':\n"
                    f"Errors:\n" + "\n".join(error_details)
                )
                raise ValidationError.from_exception_data(
                    model_class.__name__,
                    e.errors(),
                    error_msg
                ) from e
            except Exception as e:
                raise TypeError(
                    f"Failed to instantiate model '{model_class.__name__}' for parameter '{param_name}': {e}"
                ) from e
        
        # Update bound_args with model instances
        for param_name, model_instance in model_instances.items():
            bound_args.arguments[param_name] = model_instance
        
        # Call the original function with the updated arguments
        return func(*bound_args.args, **bound_args.kwargs)
    
    return wrapper


def _is_pydantic_model(type_hint: Type[Any]) -> bool:
    """Check if a type hint represents a Pydantic model.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is a Pydantic model, False otherwise.
    """
    # Handle direct class references
    if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
        return True
    
    # Handle generic types and unions
    origin = get_origin(type_hint)
    if origin is not None:
        # Check if it's a Union type with Pydantic models
        if origin is Union:
            args = get_args(type_hint)
            return any(_is_pydantic_model(arg) for arg in args)
        # Check if it's an Optional type (Union[T, None])
        elif origin is Union and len(get_args(type_hint)) == 2:
            args = get_args(type_hint)
            if type(None) in args:
                non_none_type = next(arg for arg in args if arg is not type(None))
                return _is_pydantic_model(non_none_type)
    
    return False


def _extract_model_kwargs(model_class: Type[BaseModel], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract keyword arguments that match the fields of a Pydantic model.
    
    Args:
        model_class: The Pydantic model class.
        kwargs: The available keyword arguments.
        
    Returns:
        Dictionary of kwargs that match the model fields.
    """
    model_kwargs = {}
    
    # Get the model fields
    if hasattr(model_class, 'model_fields'):
        model_fields = model_class.model_fields
    else:
        # Fallback for older Pydantic versions
        model_fields = getattr(model_class, '__fields__', {})
    
    # Extract matching kwargs
    for field_name in model_fields.keys():
        if field_name in kwargs:
            model_kwargs[field_name] = kwargs[field_name]
    
    return model_kwargs


__all__ = ['model_inject']
