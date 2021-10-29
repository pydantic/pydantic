# output-json
from typing import Dict, Any, Type
from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int
    title: str

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type['Person']) -> None:
            props = schema.get('properties', {})
            props.pop('title', None)


print(Person.schema_json(indent=2))
