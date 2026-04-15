Color definitions are used as per the CSS3 [CSS Color Module Level 3](http://www.w3.org/TR/css3-color/#svg-color) specification.

A few colors have multiple names referring to the same colors, e.g. `grey` and `gray` or `aqua` and `cyan`.

In these cases the *last* color when sorted alphabetically takes precedence. eg. `Color((0, 255, 255)).as_named() == 'cyan'` because "cyan" comes after "aqua".

## RGBA

```python
RGBA(r: float, g: float, b: float, alpha: float | None)

```

Internal use only as a representation of a color.

Source code in `pydantic_extra_types/color.py`

```python
def __init__(self, r: float, g: float, b: float, alpha: float | None):
    self.r = r
    self.g = g
    self.b = b
    self.alpha = alpha

    self._tuple: tuple[float, float, float, float | None] = (r, g, b, alpha)

```

## Color

```python
Color(value: ColorType)

```

Bases: `Representation`

Represents a color.

Source code in `pydantic_extra_types/color.py`

```python
def __init__(self, value: ColorType) -> None:
    self._rgba: RGBA
    self._original: ColorType
    if isinstance(value, (tuple, list)):
        self._rgba = parse_tuple(value)
    elif isinstance(value, str):
        self._rgba = parse_str(value)
    elif isinstance(value, Color):
        self._rgba = value._rgba
        value = value._original
    else:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: value must be a tuple, list or string',
        )

    # if we've got here value must be a valid color
    self._original = value

```

### original

```python
original() -> ColorType

```

Original value passed to `Color`.

Source code in `pydantic_extra_types/color.py`

```python
def original(self) -> ColorType:
    """Original value passed to `Color`."""
    return self._original

```

### as_named

```python
as_named(*, fallback: bool = False) -> str

```

Returns the name of the color if it can be found in `COLORS_BY_VALUE` dictionary, otherwise returns the hexadecimal representation of the color or raises `ValueError`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `fallback` | `bool` | If True, falls back to returning the hexadecimal representation of the color instead of raising a ValueError when no named color is found. | `False` |

Returns:

| Type | Description | | --- | --- | | `str` | The name of the color, or the hexadecimal representation of the color. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | When no named color is found and fallback is False. |

Source code in `pydantic_extra_types/color.py`

```python
def as_named(self, *, fallback: bool = False) -> str:
    """Returns the name of the color if it can be found in `COLORS_BY_VALUE` dictionary,
    otherwise returns the hexadecimal representation of the color or raises `ValueError`.

    Args:
        fallback: If True, falls back to returning the hexadecimal representation of
            the color instead of raising a ValueError when no named color is found.

    Returns:
        The name of the color, or the hexadecimal representation of the color.

    Raises:
        ValueError: When no named color is found and fallback is `False`.
    """
    if self._rgba.alpha is not None:
        return self.as_hex()
    rgb = cast('tuple[int, int, int]', self.as_rgb_tuple())

    if rgb in COLORS_BY_VALUE:
        return COLORS_BY_VALUE[rgb]
    else:
        if fallback:
            return self.as_hex()
        else:
            raise ValueError('no named color found, use fallback=True, as_hex() or as_rgb()')

```

### as_hex

```python
as_hex(format: Literal['short', 'long'] = 'short') -> str

```

Returns the hexadecimal representation of the color.

Hex string representing the color can be 3, 4, 6, or 8 characters depending on whether the string a "short" representation of the color is possible and whether there's an alpha channel.

Returns:

| Type | Description | | --- | --- | | `str` | The hexadecimal representation of the color. |

Source code in `pydantic_extra_types/color.py`

```python
def as_hex(self, format: Literal['short', 'long'] = 'short') -> str:
    """Returns the hexadecimal representation of the color.

    Hex string representing the color can be 3, 4, 6, or 8 characters depending on whether the string
    a "short" representation of the color is possible and whether there's an alpha channel.

    Returns:
        The hexadecimal representation of the color.
    """
    values = [float_to_255(c) for c in self._rgba[:3]]
    if self._rgba.alpha is not None:
        values.append(float_to_255(self._rgba.alpha))

    as_hex = ''.join(f'{v:02x}' for v in values)
    if format == 'short' and all(c in repeat_colors for c in values):
        as_hex = ''.join(as_hex[c] for c in range(0, len(as_hex), 2))
    return f'#{as_hex}'

```

### as_rgb

```python
as_rgb() -> str

```

Color as an `rgb(<r>, <g>, <b>)` or `rgba(<r>, <g>, <b>, <a>)` string.

Source code in `pydantic_extra_types/color.py`

```python
def as_rgb(self) -> str:
    """Color as an `rgb(<r>, <g>, <b>)` or `rgba(<r>, <g>, <b>, <a>)` string."""
    if self._rgba.alpha is None:
        return f'rgb({float_to_255(self._rgba.r)}, {float_to_255(self._rgba.g)}, {float_to_255(self._rgba.b)})'
    else:
        return (
            f'rgba({float_to_255(self._rgba.r)}, {float_to_255(self._rgba.g)}, {float_to_255(self._rgba.b)}, '
            f'{round(self._alpha_float(), 2)})'
        )

```

### as_rgb_tuple

```python
as_rgb_tuple(*, alpha: bool | None = None) -> ColorTuple

```

Returns the color as an RGB or RGBA tuple.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `alpha` | `bool | None` | Whether to include the alpha channel. There are three options for this input: None (default): Include alpha only if it's set. (e.g. not None) True: Always include alpha. False: Always omit alpha. | `None` |

Returns:

| Type | Description | | --- | --- | | `ColorTuple` | A tuple that contains the values of the red, green, and blue channels in the range 0 to 255. If alpha is included, it is in the range 0 to 1. |

Source code in `pydantic_extra_types/color.py`

```python
def as_rgb_tuple(self, *, alpha: bool | None = None) -> ColorTuple:
    """Returns the color as an RGB or RGBA tuple.

    Args:
        alpha: Whether to include the alpha channel. There are three options for this input:

            - `None` (default): Include alpha only if it's set. (e.g. not `None`)
            - `True`: Always include alpha.
            - `False`: Always omit alpha.

    Returns:
        A tuple that contains the values of the red, green, and blue channels in the range 0 to 255.
            If alpha is included, it is in the range 0 to 1.
    """
    r, g, b = (float_to_255(c) for c in self._rgba[:3])
    if alpha is None and self._rgba.alpha is None or alpha is not None and not alpha:
        return r, g, b
    else:
        return r, g, b, self._alpha_float()

```

### as_hsl

```python
as_hsl() -> str

```

Color as an `hsl(<h>, <s>, <l>)` or `hsl(<h>, <s>, <l>, <a>)` string.

Source code in `pydantic_extra_types/color.py`

```python
def as_hsl(self) -> str:
    """Color as an `hsl(<h>, <s>, <l>)` or `hsl(<h>, <s>, <l>, <a>)` string."""
    if self._rgba.alpha is None:
        h, s, li = self.as_hsl_tuple(alpha=False)  # type: ignore
        return f'hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%})'
    else:
        h, s, li, a = self.as_hsl_tuple(alpha=True)  # type: ignore
        return f'hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%}, {round(a, 2)})'

```

### as_hsl_tuple

```python
as_hsl_tuple(*, alpha: bool | None = None) -> HslColorTuple

```

Returns the color as an HSL or HSLA tuple.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `alpha` | `bool | None` | Whether to include the alpha channel. None (default): Include the alpha channel only if it's set (e.g. not None). True: Always include alpha. False: Always omit alpha. | `None` |

Returns:

| Type | Description | | --- | --- | | `HslColorTuple` | The color as a tuple of hue, saturation, lightness, and alpha (if included). All elements are in the range 0 to 1. |

Note

This is HSL as used in HTML and most other places, not HLS as used in Python's `colorsys`.

Source code in `pydantic_extra_types/color.py`

```python
def as_hsl_tuple(self, *, alpha: bool | None = None) -> HslColorTuple:
    """Returns the color as an HSL or HSLA tuple.

    Args:
        alpha: Whether to include the alpha channel.

            - `None` (default): Include the alpha channel only if it's set (e.g. not `None`).
            - `True`: Always include alpha.
            - `False`: Always omit alpha.

    Returns:
        The color as a tuple of hue, saturation, lightness, and alpha (if included).
            All elements are in the range 0 to 1.

    Note:
        This is HSL as used in HTML and most other places, not HLS as used in Python's `colorsys`.
    """
    h, l, s = rgb_to_hls(self._rgba.r, self._rgba.g, self._rgba.b)
    if alpha is None:
        if self._rgba.alpha is None:
            return h, s, l
        else:
            return h, s, l, self._alpha_float()
    return (h, s, l, self._alpha_float()) if alpha else (h, s, l)

```

## parse_tuple

```python
parse_tuple(value: tuple[Any, ...]) -> RGBA

```

Parse a tuple or list to get RGBA values.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `tuple[Any, ...]` | A tuple or list. | *required* |

Returns:

| Type | Description | | --- | --- | | `RGBA` | An RGBA tuple parsed from the input tuple. |

Raises:

| Type | Description | | --- | --- | | `PydanticCustomError` | If tuple is not valid. |

Source code in `pydantic_extra_types/color.py`

```python
def parse_tuple(value: tuple[Any, ...]) -> RGBA:
    """Parse a tuple or list to get RGBA values.

    Args:
        value: A tuple or list.

    Returns:
        An `RGBA` tuple parsed from the input tuple.

    Raises:
        PydanticCustomError: If tuple is not valid.
    """
    if len(value) == 3:
        r, g, b = (parse_color_value(v) for v in value)
        return RGBA(r, g, b, None)
    elif len(value) == 4:
        r, g, b = (parse_color_value(v) for v in value[:3])
        return RGBA(r, g, b, parse_float_alpha(value[3]))
    else:
        raise PydanticCustomError('color_error', 'value is not a valid color: tuples must have length 3 or 4')

```

## parse_str

```python
parse_str(value: str) -> RGBA

```

Parse a string representing a color to an RGBA tuple.

Possible formats for the input string include:

- named color, see `COLORS_BY_NAME`
- hex short eg. `<prefix>fff` (prefix can be `#`, `0x` or nothing)
- hex long eg. `<prefix>ffffff` (prefix can be `#`, `0x` or nothing)
- `rgb(<r>, <g>, <b>)`
- `rgba(<r>, <g>, <b>, <a>)`
- `transparent`

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `str` | A string representing a color. | *required* |

Returns:

| Type | Description | | --- | --- | | `RGBA` | An RGBA tuple parsed from the input string. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If the input string cannot be parsed to an RGBA tuple. |

Source code in `pydantic_extra_types/color.py`

```python
def parse_str(value: str) -> RGBA:
    """Parse a string representing a color to an RGBA tuple.

    Possible formats for the input string include:

    * named color, see `COLORS_BY_NAME`
    * hex short eg. `<prefix>fff` (prefix can be `#`, `0x` or nothing)
    * hex long eg. `<prefix>ffffff` (prefix can be `#`, `0x` or nothing)
    * `rgb(<r>, <g>, <b>)`
    * `rgba(<r>, <g>, <b>, <a>)`
    * `transparent`

    Args:
        value: A string representing a color.

    Returns:
        An `RGBA` tuple parsed from the input string.

    Raises:
        ValueError: If the input string cannot be parsed to an RGBA tuple.
    """
    value_lower = value.lower()
    if value_lower in COLORS_BY_NAME:
        r, g, b = COLORS_BY_NAME[value_lower]
        return ints_to_rgba(r, g, b, None)

    m = re.fullmatch(r_hex_short, value_lower)
    if m:
        *rgb, a = m.groups()
        r, g, b = (int(v * 2, 16) for v in rgb)
        alpha = int(a * 2, 16) / 255 if a else None
        return ints_to_rgba(r, g, b, alpha)

    m = re.fullmatch(r_hex_long, value_lower)
    if m:
        *rgb, a = m.groups()
        r, g, b = (int(v, 16) for v in rgb)
        alpha = int(a, 16) / 255 if a else None
        return ints_to_rgba(r, g, b, alpha)

    m = re.fullmatch(r_rgb, value_lower) or re.fullmatch(r_rgb_v4_style, value_lower)
    if m:
        return ints_to_rgba(*m.groups())  # type: ignore

    m = re.fullmatch(r_hsl, value_lower) or re.fullmatch(r_hsl_v4_style, value_lower)
    if m:
        return parse_hsl(*m.groups())  # type: ignore

    if value_lower == 'transparent':
        return RGBA(0, 0, 0, 0)

    raise PydanticCustomError(
        'color_error',
        'value is not a valid color: string not recognised as a valid color',
    )

```

## ints_to_rgba

```python
ints_to_rgba(
    r: int | str,
    g: int | str,
    b: int | str,
    alpha: float | None = None,
) -> RGBA

```

Converts integer or string values for RGB color and an optional alpha value to an `RGBA` object.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `r` | `int | str` | An integer or string representing the red color value. | *required* | | `g` | `int | str` | An integer or string representing the green color value. | *required* | | `b` | `int | str` | An integer or string representing the blue color value. | *required* | | `alpha` | `float | None` | A float representing the alpha value. Defaults to None. | `None` |

Returns:

| Type | Description | | --- | --- | | `RGBA` | An instance of the RGBA class with the corresponding color and alpha values. |

Source code in `pydantic_extra_types/color.py`

```python
def ints_to_rgba(
    r: int | str,
    g: int | str,
    b: int | str,
    alpha: float | None = None,
) -> RGBA:
    """Converts integer or string values for RGB color and an optional alpha value to an `RGBA` object.

    Args:
        r: An integer or string representing the red color value.
        g: An integer or string representing the green color value.
        b: An integer or string representing the blue color value.
        alpha: A float representing the alpha value. Defaults to None.

    Returns:
        An instance of the `RGBA` class with the corresponding color and alpha values.
    """
    return RGBA(
        parse_color_value(r),
        parse_color_value(g),
        parse_color_value(b),
        parse_float_alpha(alpha),
    )

```

## parse_color_value

```python
parse_color_value(
    value: int | str, max_val: int = 255
) -> float

```

Parse the color value provided and return a number between 0 and 1.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `int | str` | An integer or string color value. | *required* | | `max_val` | `int` | Maximum range value. Defaults to 255. | `255` |

Raises:

| Type | Description | | --- | --- | | `PydanticCustomError` | If the value is not a valid color. |

Returns:

| Type | Description | | --- | --- | | `float` | A number between 0 and 1. |

Source code in `pydantic_extra_types/color.py`

```python
def parse_color_value(value: int | str, max_val: int = 255) -> float:
    """Parse the color value provided and return a number between 0 and 1.

    Args:
        value: An integer or string color value.
        max_val: Maximum range value. Defaults to 255.

    Raises:
        PydanticCustomError: If the value is not a valid color.

    Returns:
        A number between 0 and 1.
    """
    try:
        color = float(value)
    except (ValueError, TypeError) as e:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: color values must be a valid number',
        ) from e
    if 0 <= color <= max_val:
        return color / max_val
    else:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: color values must be in the range 0 to {max_val}',
            {'max_val': max_val},
        )

```

## parse_float_alpha

```python
parse_float_alpha(
    value: None | str | float | int,
) -> float | None

```

Parse an alpha value checking it's a valid float in the range 0 to 1.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `None | str | float | int` | The input value to parse. | *required* |

Returns:

| Type | Description | | --- | --- | | `float | None` | The parsed value as a float, or None if the value was None or equal 1. |

Raises:

| Type | Description | | --- | --- | | `PydanticCustomError` | If the input value cannot be successfully parsed as a float in the expected range. |

Source code in `pydantic_extra_types/color.py`

```python
def parse_float_alpha(value: None | str | float | int) -> float | None:
    """Parse an alpha value checking it's a valid float in the range 0 to 1.

    Args:
        value: The input value to parse.

    Returns:
        The parsed value as a float, or `None` if the value was None or equal 1.

    Raises:
        PydanticCustomError: If the input value cannot be successfully parsed as a float in the expected range.
    """
    if value is None:
        return None
    try:
        if isinstance(value, str) and value.endswith('%'):
            alpha = float(value[:-1]) / 100
        else:
            alpha = float(value)
    except ValueError as e:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: alpha values must be a valid float',
        ) from e

    if math.isclose(alpha, 1):
        return None
    elif 0 <= alpha <= 1:
        return alpha
    else:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: alpha values must be in the range 0 to 1',
        )

```

## parse_hsl

```python
parse_hsl(
    h: str,
    h_units: str,
    sat: str,
    light: str,
    alpha: float | None = None,
) -> RGBA

```

Parse raw hue, saturation, lightness, and alpha values and convert to RGBA.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `h` | `str` | The hue value. | *required* | | `h_units` | `str` | The unit for hue value. | *required* | | `sat` | `str` | The saturation value. | *required* | | `light` | `str` | The lightness value. | *required* | | `alpha` | `float | None` | Alpha value. | `None` |

Returns:

| Type | Description | | --- | --- | | `RGBA` | An instance of RGBA. |

Source code in `pydantic_extra_types/color.py`

```python
def parse_hsl(h: str, h_units: str, sat: str, light: str, alpha: float | None = None) -> RGBA:
    """Parse raw hue, saturation, lightness, and alpha values and convert to RGBA.

    Args:
        h: The hue value.
        h_units: The unit for hue value.
        sat: The saturation value.
        light: The lightness value.
        alpha: Alpha value.

    Returns:
        An instance of `RGBA`.
    """
    s_value, l_value = parse_color_value(sat, 100), parse_color_value(light, 100)

    h_value = float(h)
    if h_units in {None, 'deg'}:
        h_value = h_value % 360 / 360
    elif h_units == 'rad':
        h_value = h_value % rads / rads
    else:
        # turns
        h_value %= 1

    r, g, b = hls_to_rgb(h_value, l_value, s_value)
    return RGBA(r, g, b, parse_float_alpha(alpha))

```

## float_to_255

```python
float_to_255(c: float) -> int

```

Converts a float value between 0 and 1 (inclusive) to an integer between 0 and 255 (inclusive).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `c` | `float` | The float value to be converted. Must be between 0 and 1 (inclusive). | *required* |

Returns:

| Type | Description | | --- | --- | | `int` | The integer equivalent of the given float value rounded to the nearest whole number. |

Source code in `pydantic_extra_types/color.py`

```python
def float_to_255(c: float) -> int:
    """Converts a float value between 0 and 1 (inclusive) to an integer between 0 and 255 (inclusive).

    Args:
        c: The float value to be converted. Must be between 0 and 1 (inclusive).

    Returns:
        The integer equivalent of the given float value rounded to the nearest whole number.
    """
    return round(c * 255)

```
