# output-json
from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int

    class Config:
        schema_extra = {
            'examples': [
                {
                    'name': 'John Doe',
                    'age': 25,
                }
            ]
        }


print(Person.schema_json(indent=2))
