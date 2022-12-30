from typing import List, Dict
from pydantic import BaseModel, ValidationError


class Pets(BaseModel):
    __root__: List[str]


print(Pets.model_validate(['dog', 'cat']))
print(Pets.model_validate({'__root__': ['dog', 'cat']}))  # not recommended


class PetsByName(BaseModel):
    __root__: Dict[str, str]


print(PetsByName.model_validate({'Otis': 'dog', 'Milo': 'cat'}))
try:
    PetsByName.model_validate({'__root__': {'Otis': 'dog', 'Milo': 'cat'}})
except ValidationError as e:
    print(e)
