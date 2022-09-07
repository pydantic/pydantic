# output-json
import json
from pydantic import BaseModel
from pydantic.schema import schema


class Foo(BaseModel):
    a: str = None


class Model(BaseModel):
    b: Foo


class Bar(BaseModel):
    c: int


top_level_schema = schema([Model, Bar], title='My Schema')
print(json.dumps(top_level_schema, indent=2))
