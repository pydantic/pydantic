from pydantic import BaseModel, Color, ValidationError

class Model(BaseModel):
    color: Color = None

c_named = Model(color='Black').color
c_hex_3_prefix_zero = Model(color='0x000').color
c_tuple_3 = Model(color=(0, 0, 0)).color

print(c_named.as_named_color())
# > black
print(c_named.as_hex(prefix='#', reduce=False))
# > #000000
print(c_named.as_tuple(alpha=True))
# > (0, 0, 0, 1.0)
print(c_named.as_rgb(alpha=False))
# > rgb(0, 0, 0)
print(c_named.as_hls())
# > (0.0, 0.0, 0.0)

try:
    Model(color='hello')
except ValidationError as e:
    print(e)
"""
1 validation error
color
  value is not a valid color (type=value_error.color)
"""
