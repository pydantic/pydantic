from pydantic import BaseModel, Field, PositiveInt

try:
    # this won't works since PositiveInt takes precedence over the
    # constraints defined in Field meaning they're ignored
    class Model(BaseModel):
        foo: PositiveInt = Field(..., lt=10)
except ValueError as e:
    print(e)

# but you can set the schema attribute directly:
# (Note: here exclusiveMaximum will not be enforce)
class Model(BaseModel):
    foo: PositiveInt = Field(..., exclusiveMaximum=10)

print(Model.schema())
