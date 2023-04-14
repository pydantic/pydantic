
`Color` parses HTML and CSS colors.

You can use the `Color` data type for storing colors as per
[CSS3 specification](http://www.w3.org/TR/css3-color/#svg-color). Colors can be defined via:

- [name](http://www.w3.org/TR/SVG11/types.html#ColorKeywords) (e.g. `"Black"`, `"azure"`)
- [hexadecimal value](https://en.wikipedia.org/wiki/Web_colors#Hex_triplet)
  (e.g. `"0x000"`, `"#FFFFFF"`, `"7fffd4"`)
- RGB/RGBA tuples (e.g. `(255, 255, 255)`, `(255, 255, 255, 0.5)`)
- [RGB/RGBA strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#RGB_colors)
  (e.g. `"rgb(255, 255, 255)"`, `"rgba(255, 255, 255, 0.5)"`)
- [HSL strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#HSL_colors)
  (e.g. `"hsl(270, 60%, 70%)"`, `"hsl(270, 60%, 70%, .5)"`)

```py
from pydantic import BaseModel, ValidationError
from pydantic.color import Color

c = Color('ff00ff')
print(c.as_named())
#> magenta
print(c.as_hex())
#> #f0f
c2 = Color('green')
print(c2.as_rgb_tuple())
#> (0, 128, 0)
print(c2.original())
#> green
print(repr(Color('hsl(180, 100%, 50%)')))
#> Color('cyan', rgb=(0, 255, 255))


class Model(BaseModel):
    color: Color


print(Model(color='purple'))
#> color=Color('purple', rgb=(128, 0, 128))
try:
    Model(color='hello')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    color
      value is not a valid color: string not recognised as a valid color [type=color_error, input_value='hello', input_type=str]
    """
```

`Color` has the following methods:

**`original`**
: the original string or tuple passed to `Color`

**`as_named`**
: returns a named CSS3 color; fails if the alpha channel is set or no such color exists unless
  `fallback=True` is supplied, in which case it falls back to `as_hex`

**`as_hex`**
: returns a string in the format `#fff` or `#ffffff`; will contain 4 (or 8) hex values if the alpha channel is set,
  e.g. `#7f33cc26`

**`as_rgb`**
: returns a string in the format `rgb(<red>, <green>, <blue>)`, or `rgba(<red>, <green>, <blue>, <alpha>)`
  if the alpha channel is set

**`as_rgb_tuple`**
: returns a 3- or 4-tuple in RGB(a) format. The `alpha` keyword argument can be used to define whether
  the alpha channel should be included;
  options: `True` - always include, `False` - never include, `None` (default) - include if set

**`as_hsl`**
: string in the format `hsl(<hue deg>, <saturation %>, <lightness %>)`
  or `hsl(<hue deg>, <saturation %>, <lightness %>, <alpha>)` if the alpha channel is set

**`as_hsl_tuple`**
: returns a 3- or 4-tuple in HSL(a) format. The `alpha` keyword argument can be used to define whether
  the alpha channel should be included;
  options: `True` - always include, `False` - never include, `None` (the default)  - include if set

The `__str__` method for `Color` returns `self.as_named(fallback=True)`.

!!! note
    the `as_hsl*` refer to hue, saturation, lightness "HSL" as used in html and most of the world, **not**
    "HLS" as used in Python's `colorsys`.
