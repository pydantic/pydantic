from pydantic import BaseModel, ValidationError


# This is not a pydantic model, it's an arbitrary class
class Pet:
    def __init__(self, name: str):
        self.name = name


class Model(BaseModel):
    pet: Pet
    owner: str

    class Config:
        arbitrary_types_allowed = True


pet = Pet(name='Hedwig')
# A simple check of instance type is used to validate the data
model = Model(owner='Harry', pet=pet)
print(model)
print(model.pet)
print(model.pet.name)
print(type(model.pet))
try:
    # If the value is not an instance of the type, it's invalid
    Model(owner='Harry', pet='Hedwig')
except ValidationError as e:
    print(e)
# Nothing in the instance of the arbitrary type is checked
# Here name probably should have been a str, but it's not validated
pet2 = Pet(name=42)
model2 = Model(owner='Harry', pet=pet2)
print(model2)
print(model2.pet)
print(model2.pet.name)
print(type(model2.pet))
