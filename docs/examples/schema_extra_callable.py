# output-json
from typing import Dict, Any, Type
from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int

    class Config:
        # TODO: This is no longer valid in v2;
        #   update example to use __pydantic_update_json_schema__
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type['Person']) -> None:
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)


print(Person.schema_json(indent=2))
