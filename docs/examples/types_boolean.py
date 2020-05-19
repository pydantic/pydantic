from pydantic import BaseModel, ValidationError


class BooleanModel(BaseModel):
    bool_value: bool


print(BooleanModel(bool_value=False))
print(BooleanModel(bool_value='False'))
try:
    BooleanModel(bool_value=[])
except ValidationError as e:
    print(str(e))
