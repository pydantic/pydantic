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
            reqs = schema.get('required', [])
            if 'title' in reqs:
                reqs.remove('title')


print(Person.schema_json(indent=2))
