from pydantic import BaseModel, ImportString


class ImportThingsWithDefault(BaseModel):
    obj: ImportString = 'math.cos'


# Using A default value doesn't cause automatic an import
my_cos = ImportThingsWithDefault()
print(my_cos.obj, type(my_cos.obj))

try:
    cos_of_0 = my_cos.obj(0)
except (NameError, TypeError) as e:
    print(e)


# Typically, you can overcome this with config settings
# Unfortunately this does not work here.
class ImportThingsWithDefaultValidated(BaseModel):
    obj: ImportString = 'math.cos'

    class Config:
        validate_all = True


my_cos_v = ImportThingsWithDefaultValidated()
print(my_cos_v.obj, type(my_cos_v.obj))

try:
    cos_of_0 = my_cos_v.obj(0)
except (NameError, TypeError) as e:
    print(e)
