from pydantic import BaseModel, BaseSettings


class DeepSubModel(BaseModel):
    v4: str


class SubModel(BaseModel):
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    v0: str
    sub_model: SubModel

    class Config:
        env_nested_delimiter = '__'


print(Settings().dict())
