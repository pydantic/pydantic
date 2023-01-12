# output-json
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class Person(BaseModel):
    name: str
    age: int = Field(lt=100, gt=0)
    test: Optional[int] = 0

    # class Config:
    #     schema_extra = {
    #         'examples': [
    #             {
    #                 'name': 'John Doe',
    #                 'age': 25,
    #             }
    #         ]
    #     }

data = {
    'name': 'Kenneth Reitz',
    'age': 34,
}

# 'inner_schema': {'fields': {'age': {'required': True,
#                         'schema': {'type': 'int'}},
#                 'metadata': {'required': True,
#                             'schema': {'type': 'dict'}},
#                 'name': {'required': True,
#                         'schema': {'type': 'str'}}},
# Person.model_rebuild()
p = Person(**data)


# print(p)
from pprint import pprint

pprint(p.json_schema())


# print(Person.schema_json(indent=2))
