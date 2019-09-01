from typing import List
import json
from pydantic import BaseModel
from pydantic.schema import schema

class Pets(BaseModel):
    __root__: List[str]

print(Pets(__root__=['dog', 'cat']))
# > Pets __root__=['dog', 'cat']

print(Pets(__root__=['dog', 'cat']).json())
# ["dog", "cat"]

print(Pets.parse_obj(['dog', 'cat']))
# > Pets __root__=['dog', 'cat']

print(Pets.schema())
# > {'title': 'Pets', 'type': 'array', 'items': {'type': 'string'}}

pets_schema = schema([Pets])
print(json.dumps(pets_schema, indent=2))
"""
{
  "definitions": {
    "Pets": {
      "title": "Pets",
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
"""
