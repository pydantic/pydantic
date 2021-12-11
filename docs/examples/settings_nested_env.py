import os

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


os.environ.update({
    'top': '{"v1": "1", "v2": "2"}',
    'v0': 0,
    'top__v3': 3,
    'top__sub': '{"sub_sub": {"v6": "6"}}',
    'top__sub__v4': 4,
    'top__sub__v5': 5,
})


print(Settings())
