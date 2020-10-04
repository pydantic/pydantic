from pydantic import create_model, validator


def username_alphanumeric(cls, v):
    assert v.isalnum(), 'must be alphanumeric'
    return v


validators = {
    'username_validator':
    validator('username')(username_alphanumeric)
}

WithValidatorModel = create_model(
    'WithValidatorModel',
    username=(str, ...),
    __validators__=validators
)
