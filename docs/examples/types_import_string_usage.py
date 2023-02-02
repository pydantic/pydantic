from pydantic import BaseModel, ImportString, ValidationError


class ImportThings(BaseModel):
    obj: ImportString


# A string value will cause an automatic import
my_cos = ImportThings(obj='math.cos')

# You can use the imported function as you would expect
cos_of_0 = my_cos.obj(0)
assert cos_of_0 == 1


# A string whose value cannot be imported will raise an error
try:
    ImportThings(obj='foo.bar')
except ValidationError as e:
    print(e)


# An object defined in the current namespace can indeed be imported,
# though you should probably avoid doing this (since the ordering of declaration
# can have an impact on behavior).
class Foo:
    bar = 1


# This now works
my_foo = ImportThings(obj=Foo)
# So does this
my_foo_2 = ImportThings(obj='__main__.Foo')


# Actual python objects can be assigned as well
from math import cos  # noqa: E402
my_cos = ImportThings(obj=cos)
my_cos_2 = ImportThings(obj='math.cos')
assert my_cos == my_cos_2
