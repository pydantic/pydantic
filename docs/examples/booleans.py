from pydantic import BaseModel, StrictBool, ValidationError


class BooleansModel(BaseModel):
    standard: bool
    strict: StrictBool


print(BooleansModel(standard=False, strict=False))
# BooleansModel relaxed=False standard=False strict=False

print(BooleansModel(standard='False', strict=False))
# BooleansModel relaxed=True standard=False strict=False

try:
    BooleansModel(standard='False', strict='False')
except ValidationError as e:
    print(str(e))
"""
1 validation error
strict
  value is not a valid boolean (type=value_error.strictbool)
"""

print(BooleansModel(standard='False', strict=False))
# BooleansModel relaxed=False standard=False strict=False
try:
    BooleansModel(standard=[], strict=False)
except ValidationError as e:
    print(str(e))
"""
1 validation error
standard
  value could not be parsed to a boolean (type=type_error.bool)
"""
