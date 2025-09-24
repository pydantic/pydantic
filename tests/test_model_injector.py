"""Tests for the model_inject decorator."""

import pytest
from pydantic import BaseModel, Field, ValidationError, model_inject


class UserModel(BaseModel):
    """Simple user model for testing."""
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")
    email: str = Field(..., description="User's email")


class SettingsModel(BaseModel):
    """Settings model for testing."""
    theme: str = Field(default="light", description="UI theme")
    language: str = Field(default="en", description="Language preference")


class TestModelInjector:
    """Test the model_inject decorator."""

    def test_single_model_parameter(self):
        """Test decorator with a single model parameter."""
        
        @model_inject
        def process_user(user: UserModel) -> str:
            return f"Processing user: {user.name}"
        
        result = process_user(  # type: ignore
            name="John Doe",
            age=30,
            email="john@example.com"
        )
        
        assert result == "Processing user: John Doe"
    
    def test_multiple_model_parameters(self):
        """Test decorator with multiple model parameters."""
        
        @model_inject
        def setup_user(user: UserModel, settings: SettingsModel) -> dict:
            return {
                "user_name": user.name,
                "user_age": user.age,
                "theme": settings.theme,
                "language": settings.language
            }
        
        result = setup_user(  # type: ignore
            name="Jane Smith",
            age=25,
            email="jane@example.com",
            theme="dark",
            language="es"
        )
        
        assert result["user_name"] == "Jane Smith"
        assert result["user_age"] == 25
        assert result["theme"] == "dark"
        assert result["language"] == "es"
    
    def test_mixed_parameters(self):
        """Test decorator with mixed model and regular parameters."""
        
        @model_inject
        def update_user(user: UserModel, admin_notes: str, force_update: bool = False) -> dict:
            return {
                "user_name": user.name,
                "admin_notes": admin_notes,
                "force_update": force_update
            }
        
        result = update_user(  # type: ignore
            name="Bob Wilson",
            age=35,
            email="bob@example.com",
            admin_notes="Updated user preferences",
            force_update=True
        )
        
        assert result["user_name"] == "Bob Wilson"
        assert result["admin_notes"] == "Updated user preferences"
        assert result["force_update"] is True
    
    def test_no_model_parameters(self):
        """Test decorator with no model parameters (should work normally)."""
        
        @model_inject
        def regular_function(x: int, y: str) -> str:
            return f"{x} - {y}"
        
        result = regular_function(x=42, y="hello")
        assert result == "42 - hello"
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields."""
        
        @model_inject
        def process_user(user: UserModel) -> str:
            return f"Processing user: {user.name}"
        
        with pytest.raises(ValidationError) as exc_info:
            process_user(  # type: ignore
                name="John Doe",
                # Missing required fields: age, email
            )
        
        error = exc_info.value
        assert "Validation failed for model 'UserModel'" in str(error)
        assert "age" in str(error) or "email" in str(error)
    
    def test_invalid_field_types(self):
        """Test error handling for invalid field types."""
        
        @model_inject
        def process_user(user: UserModel) -> str:
            return f"Processing user: {user.name}"
        
        with pytest.raises(ValidationError) as exc_info:
            process_user(  # type: ignore
                name="John Doe",
                age="not_a_number",  # Should be int
                email="john@example.com"
            )
        
        error = exc_info.value
        assert "Validation failed for model 'UserModel'" in str(error)
        assert "age" in str(error)
    
    def test_function_signature_preservation(self):
        """Test that the original function signature is preserved."""
        
        @model_inject
        def test_function(user: UserModel, x: int, y: str = "default") -> str:
            """Test function with docstring."""
            return f"{user.name} - {x} - {y}"
        
        # Check that the function signature is preserved
        import inspect
        sig = inspect.signature(test_function)
        params = list(sig.parameters.keys())
        
        assert "user" in params
        assert "x" in params
        assert "y" in params
        
        # Check that the docstring is preserved
        assert test_function.__doc__ == "Test function with docstring."
        
        # Check that the function name is preserved
        assert test_function.__name__ == "test_function"

    def test_positional_dict_argument(self):
        @model_inject
        def process_user(user: UserModel) -> str:
            return f'Processing user: {user.name}'

        result = process_user({
            'name': 'John Doe',
            'age': 30,
            'street': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'postal_code': '10001',
            'email': 'john@example.com',
        })
        assert result == 'Processing user: John Doe'

    def test_positional_single_value(self):
        class SimpleUser(BaseModel):
            name: str
            age: int = 25

        @model_inject
        def greet_user(user: SimpleUser) -> str:
            return f'Hello {user.name}, age {user.age}'

        result = greet_user('Alice')
        assert result == 'Hello Alice, age 25'

    def test_multiple_positional_arguments(self):
        @model_inject
        def setup_user_and_settings(user: UserModel, settings: SettingsModel) -> dict:
            return {
                'user_name': user.name,
                'user_age': user.age,
                'theme': settings.theme,
                'language': settings.language,
            }

        result = setup_user_and_settings(
            {
                'name': 'Jane Smith',
                'age': 25,
                'street': '456 Oak Ave',
                'city': 'Los Angeles',
                'state': 'CA',
                'postal_code': '90210',
                'email': 'jane@example.com',
            },
            {
                'theme': 'dark',
                'language': 'es',
            }
        )
        assert result['user_name'] == 'Jane Smith'
        assert result['user_age'] == 25
        assert result['theme'] == 'dark'
        assert result['language'] == 'es'

    def test_mixed_positional_and_keyword(self):
        @model_inject
        def setup_user_and_settings(user: UserModel, settings: SettingsModel) -> dict:
            return {
                'user_name': user.name,
                'user_age': user.age,
                'theme': settings.theme,
                'language': settings.language,
            }

        result = setup_user_and_settings(
            {
                'name': 'Bob Wilson',
                'age': 35,
                'street': '789 Pine St',
                'city': 'Seattle',
                'state': 'WA',
                'postal_code': '98101',
                'email': 'bob@example.com',
            },
            theme='dark',
            language='fr'
        )
        assert result['user_name'] == 'Bob Wilson'
        assert result['user_age'] == 35
        assert result['theme'] == 'dark'
        assert result['language'] == 'fr'

    def test_multiple_positional_values_for_single_model(self):
        class Params(BaseModel):
            b: str
            c: int
            d: int

        @model_inject
        def process_params(params: Params) -> str:
            return f"b={params.b}, c={params.c}, d={params.d}"

        result = process_params("test@example.com", 2, 3)
        assert result == "b=test@example.com, c=2, d=3"

    def test_single_positional_value_for_single_model(self):
        class SimpleModel(BaseModel):
            name: str
            age: int = 25

        @model_inject
        def process_simple(model: SimpleModel) -> str:
            return f"Name: {model.name}, Age: {model.age}"

        result = process_simple("Alice")
        assert result == "Name: Alice, Age: 25"
