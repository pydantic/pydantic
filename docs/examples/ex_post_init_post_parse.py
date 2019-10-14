from datetime import datetime
from pydantic.dataclasses import dataclass

@dataclass
class Birth:
    year: int
    month: int
    day: int

@dataclass
class User:
    birth: Birth

    def __post_init__(self):
        print(self.birth)
        # > {'year': 1995, 'month': 3, 'day': 2}

    def __post_init_post_parse__(self):
        print(self.birth)
        # > Birth(year=1995, month=3, day=2)

user = User(**{'birth': {'year': 1995, 'month': 3, 'day': 2}})
