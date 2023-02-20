# output-json
from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int

    class Config:
        # TODO: This is no longer valid in v2;
        #   update example to use __pydantic_update_json_schema__
        schema_extra = {
            'examples': [
                {
                    'name': 'John Doe',
                    'age': 25,
                }
            ]
        }


print(Person.schema_json(indent=2))
