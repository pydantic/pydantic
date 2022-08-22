import os
from typing import Any, List

from pydantic import BaseSettings


class Settings(BaseSettings):
    numbers: List[int]

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == 'numbers':
                return [int(x) for x in raw_val.split(',')]
            return cls.json_loads(raw_val)


os.environ['numbers'] = '1,2,3'
print(Settings().dict())
