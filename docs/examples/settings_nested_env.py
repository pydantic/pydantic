from pydantic import BaseModel, BaseSettings


class SubSubValue(BaseModel):
    v6: str


class SubValue(BaseModel):
    v4: str
    v5: str
    sub_sub: SubSubValue


class TopValue(BaseModel):
    v1: str
    v2: str
    v3: str
    sub: SubValue


class Settings(BaseSettings):
    v0: str
    top: TopValue

    class Config:
        env_nested_delimiter = '__'


print(Settings())
