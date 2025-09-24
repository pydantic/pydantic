"""Example usage of the model_inject decorator."""

from pydantic import BaseModel, Field, model_inject, ValidationError


class UserModel(BaseModel):
    """User model for demonstration."""
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")
    email: str = Field(..., description="User's email")


class SettingsModel(BaseModel):
    """Settings model for demonstration."""
    theme: str = Field(default="light", description="UI theme")
    language: str = Field(default="en", description="Language preference")
    notifications: bool = Field(default=True, description="Enable notifications")


def basic_example():
    """Basic usage example."""
    @model_inject
    def create_user_profile(user: UserModel) -> str:
        """Create a user profile from user data."""
        return f"User: {user.name} (Age: {user.age}) - {user.email}"
    
    # Usage
    result = create_user_profile(
        name="John Doe",
        age=30,
        email="john@example.com"
    )
    print(result)  # Output: "User: John Doe (Age: 30) - john@example.com"


def multiple_models_example():
    """Multiple models example."""
    @model_inject
    def setup_application(user: UserModel, settings: SettingsModel) -> dict:
        """Setup application with user and settings."""
        return {
            "user_name": user.name,
            "user_email": user.email,
            "theme": settings.theme,
            "language": settings.language,
            "notifications": settings.notifications
        }
    
    # Usage
    result = setup_application(
        name="Jane Smith",
        age=25,
        email="jane@example.com",
        theme="dark",
        language="es",
        notifications=False
    )
    print(result)


def error_handling_example():
    """Error handling example."""
    @model_inject
    def create_user(user: UserModel) -> str:
        return f"User: {user.name}"
    
    # This will raise a ValidationError
    try:
        result = create_user(
            name="Bob Wilson",
            # Missing required fields: age, email
        )
        print(result)
    except ValidationError as e:
        print(f"Expected error: {e}")


if __name__ == "__main__":
    print("=== Model Injector Examples ===\n")
    
    print("1. Basic Example:")
    basic_example()
    
    print("\n2. Multiple Models Example:")
    multiple_models_example()
    
    print("\n3. Error Handling Example:")
    error_handling_example()
    
    print("\n4. Positional Arguments Example:")
    positional_arguments_example()


def positional_arguments_example():
    """Demonstrate positional argument support."""
    # Positional dict argument
    positional_result = create_user({
        "name": "Positional User",
        "age": 28,
        "street": "999 Positional St",
        "city": "Position City",
        "state": "PC",
        "postal_code": "99999",
        "email": "positional@example.com",
    })
    print(f"Positional dict: {positional_result}")
    
    # Positional single value (uses first field)
    single_value_result = create_user("Single Value User")
    print(f"Positional single value: {single_value_result}")
    
    # Multiple positional arguments
    multi_positional_result = setup_user_and_settings(
        {
            "name": "Multi Positional",
            "age": 32,
            "street": "888 Multi St",
            "city": "Multi City",
            "state": "MC",
            "postal_code": "88888",
            "email": "multi@example.com",
        },
        {
            "theme": "auto",
            "language": "de",
        }
    )
    print(f"Multiple positional: {multi_positional_result}")
