from pydantic import BaseModel


class Pet(BaseModel):
    name: str
    species: str


a = Pet(name='Bones', species='dog')

match a:
    # match with kwargs
    case Pet(species='dog', name=dog_name):
        print(f'{dog_name} is a dog')
    case _:
        print('No dog matched')


b = Pet(name='Orion', species='cat')

match b:
    # match with args (according to field ordering)
    case Pet(cat_name, 'cat'):
        print(f'{cat_name} is a cat')
    case _:
        print('No cat matched')
