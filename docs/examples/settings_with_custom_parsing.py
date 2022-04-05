# output-json
import os
from typing import List

from pydantic import BaseSettings, Field


def parse_list(s: str) -> List[int]:
    return [int(x.strip()) for x in s.split(',')]


class Settings(BaseSettings):
    numbers: List[int] = Field(env_parse=parse_list)


os.environ['numbers'] = '1,2,3'
print(Settings().dict())
