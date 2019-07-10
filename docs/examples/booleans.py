from pydantic import BaseModel, RelaxedBool, StrictBool, ValidationError


class BooleansModel(BaseModel):
    relaxed: RelaxedBool
    standard: bool
    strict: StrictBool


print(BooleansModel(relaxed=False, standard=False, strict=False))
# BooleansModel relaxed=False standard=False strict=False

print(BooleansModel(relaxed='False', standard='False', strict=False))
# BooleansModel relaxed=True standard=False strict=False

try:
    BooleansModel(relaxed='False', standard='False', strict='False')
except ValidationError as e:
    print(str(e))
"""
1 validation error
strict
  value is not a valid boolean (type=value_error.strictbool)
"""

print(BooleansModel(relaxed=[], standard='False', strict=False))
# BooleansModel relaxed=False standard=False strict=False
try:
    BooleansModel(relaxed=[], standard=[], strict=False)
except ValidationError as e:
    print(str(e))
"""
1 validation error
standard
  value could not be parsed to a boolean (type=type_error.bool)
"""
