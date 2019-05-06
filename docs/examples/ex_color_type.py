from pydantic import BaseModel, Color, ValidationError

class Model(BaseModel):
    color: Color = None

# Valid CSS3 colors
c_named = Model(color='Black').color
c_tuple_3 = Model(color=(255, 255, 255)).color
c_tuple_4 = Model(color=(255, 255, 255, 1.0)).color
c_hex_3_prefix_sharp = Model(color='#000').color
c_hex_3_prefix_zero = Model(color='0x000').color
c_hex_3_prefix_blank = Model(color='000').color
c_hex_6_prefix_sharp = Model(color='000000').color
c_hex_6_prefix_zero = Model(color='0x000000').color
c_hex_6_prefix_blank = Model(color='000000').color
c_rgb_str = Model(color='rgb(255, 255, 255)').color
c_rgba_str = Model(color='rgba(255, 255, 255, 1.0)').color

print(c_named.original())
# > Black
print(c_named.as_named_color())
# > black
print(c_named.as_hex())
# > 0x000
print(c_named.as_hex(prefix='#', reduce=False))
# > #000000
print(c_named.as_tuple())
# > (0, 0, 0)
print(c_named.as_tuple(alpha=True))
# > (0, 0, 0, 1.0)
print(c_named.as_rgb())
# > rgb(0, 0, 0)
print(c_named.as_rgb(alpha=True))
# > rgba(0, 0, 0, 1.0)
print(c_named.as_hls())
# > (0.0, 0.0, 0.0)

# Invalid color (i.e. not in the CSS3 list)
try:
    Model(color='hello')
except ValidationError as e:
    print(e)
"""
1 validation error
color
  value is not a valid CSS3/SVG color (type=value_error.color)
"""
