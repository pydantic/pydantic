from pydantic import BaseModel, Field, PositiveInt

try:
    # this won't work since PositiveInt takes precedence over the
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


# if you find yourself needing this, an alternative is to declare
# the constraints in Field (or you could use conint())
# here both constraints will be enforced:
class Model(BaseModel):
    # Here both constraints will be applied and the schema
    # will be generated correctly
    foo: int = Field(..., gt=0, lt=10)


print(Model.schema())
