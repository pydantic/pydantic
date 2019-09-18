from pydantic import BaseModel, ValidationError

class BooleanModel(BaseModel):
    bool_value: bool

print(BooleanModel(bool_value=False))
# BooleansModel bool_value=False

print(BooleanModel(bool_value='False'))
# BooleansModel bool_value=False

try:
    BooleanModel(bool_value=[])
except ValidationError as e:
    print(str(e))
"""
1 validation error
bool_value
  value could not be parsed to a boolean (type=type_error.bool)
"""
