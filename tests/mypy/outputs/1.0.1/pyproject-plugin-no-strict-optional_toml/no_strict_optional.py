from typing import Optional, Union

from pydantic import BaseModel, ConfigDict


class MongoSettings(BaseModel):
    MONGO_PASSWORD: Union[str, None]


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra='forbid',
        frozen=True,
    )


class HealthStatus(CustomBaseModel):
    status: str
    description: Optional[str] = None


hs = HealthStatus(status='healthy')
