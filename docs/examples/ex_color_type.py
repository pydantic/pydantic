from pydantic import BaseModel, ValidationError
from pydantic.color import Color

c = Color('ff00ff')
print(c.as_named())
#> magenta
print(c.as_hex())
#> #f0f

c2 = Color('green')
print(c2.as_tuple())
#> (0, 128, 0)
print(c2.original())
#> green

class Model(BaseModel):
    color: Color

print(Model(color='purple'))
# > Model color=<Color('purple', (128, 0, 128))>

try:
    Model(color='hello')
except ValidationError as e:
    print(e)
"""
1 validation error
color
  value is not a valid color (type=value_error.color)
"""
