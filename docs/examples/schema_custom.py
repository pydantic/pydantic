# output-json
import json
from pydantic import BaseModel
from pydantic.json_schema import schema


class Foo(BaseModel):
    a: int


class Model(BaseModel):
    a: Foo


# Default location for OpenAPI
top_level_schema = schema([Model], ref_prefix='#/components/schemas/')
print(json.dumps(top_level_schema, indent=2))
