from typing import List, Dict
from pydantic import BaseModel, ValidationError


class Pets(BaseModel):
    __root__: List[str]


print(Pets.parse_obj(['dog', 'cat']))
print(Pets.parse_obj({'__root__': ['dog', 'cat']}))  # not recommended


class PetsByName(BaseModel):
    __root__: Dict[str, str]


print(PetsByName.parse_obj({'Otis': 'dog', 'Milo': 'cat'}))
try:
    PetsByName.parse_obj({'__root__': {'Otis': 'dog', 'Milo': 'cat'}})
except ValidationError as e:
    print(e)
