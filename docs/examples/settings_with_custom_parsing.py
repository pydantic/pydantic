# output-json
from typing import Any, List

from pydantic import BaseSettings


def parse_list(s: str) -> List[int]:
    return [int(x.strip()) for x in s.split(',')]


class Settings(BaseSettings):
    numbers: List[int]

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "numbers":
                return parse_list(raw_val)
            return cls.json_loads(raw_val)


os.environ['numbers'] = '1,2,3'
print(Settings().dict())
