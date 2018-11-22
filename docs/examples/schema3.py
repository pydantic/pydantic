import json
from pydantic import BaseModel
from pydantic.schema import schema

class Foo(BaseModel):
    a: int

class Model(BaseModel):
    a: Foo


top_level_schema = schema([Model], ref_prefix='#/components/schemas/')  # Default location for OpenAPI
print(json.dumps(top_level_schema, indent=2))

# {
#   "definitions": {
#     "Foo": {
#       "title": "Foo",
#       "type": "object",
#       ...
