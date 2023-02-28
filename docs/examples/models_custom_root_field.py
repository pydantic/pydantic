from typing import List
import json
from pydantic import BaseModel
from pydantic.json_schema import schema


class Pets(BaseModel):
    __root__: List[str]


print(Pets(__root__=['dog', 'cat']))
print(Pets(__root__=['dog', 'cat']).model_dump_json())
print(Pets.model_validate(['dog', 'cat']))
print(Pets.model_json_schema())
pets_schema = schema([Pets])
print(json.dumps(pets_schema, indent=2))
