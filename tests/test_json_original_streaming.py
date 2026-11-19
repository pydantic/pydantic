from pydantic import BaseModel, Field, ValidationInfo, field_validator


def test_streamed_valid_defaults_receive_field_context() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""

    class Model(BaseModel):
        username: str = Field(default=' Alice ', validate_default=True)
        display_name: str = Field(default=' Alice ', validate_default=True)

        @field_validator('username', 'display_name')
        @classmethod
        def normalize(cls, value: str, info: ValidationInfo) -> str:
            value = value.strip()
            return value.lower() if info.field_name == 'username' else value

    assert Model.__pydantic_validator__._stream_plan_accepted
    assert Model.model_validate_json('{}').model_dump() == {'username': 'alice', 'display_name': 'Alice'}
