# output-json
import os
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    numbers: List[int] = Field(env_parse=str)

    @validator('numbers', pre=True)
    def validate_numbers(cls, s):
        return [int(x.strip()) for x in s.split(',')]


os.environ['numbers'] = '1,2,3'
print(Settings().dict())
