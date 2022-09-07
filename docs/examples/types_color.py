from pydantic import BaseModel, ValidationError
from pydantic.color import Color

c = Color('ff00ff')
print(c.as_named())
print(c.as_hex())
c2 = Color('green')
print(c2.as_rgb_tuple())
print(c2.original())
print(repr(Color('hsl(180, 100%, 50%)')))


class Model(BaseModel):
    color: Color


print(Model(color='purple'))
try:
    Model(color='hello')
except ValidationError as e:
    print(e)
