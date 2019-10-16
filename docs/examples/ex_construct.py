from pydantic import BaseModel, ValidationError

class Model(BaseModel):
    a: int

valid_data = dict(a=5)
invalid_data = dict(a="dog")

# Validate the model at instantiation
m = Model(**valid_data)
print(m)
try:
    Model(**invalid_data)
except ValidationError as e:
    print(e)

# Instantiate the model without validation
c = Model.construct(values=valid_data, fields_set=None)
print(c)
c = Model.construct(values=invalid_data, fields_set=None)
print(c)
