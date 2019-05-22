"""
Color definitions are  used as per CSS3 specification:
http://www.w3.org/TR/css3-color/#svg-color

A few colors have multiple names referring to the sames colors, eg. `grey` and `gray` or `aqua` and `cyan`.

In these cases the LAST color when sorted alphabetically takes preferences,
eg. Color((0, 255, 255)).as_named() == 'cyan' because "cyan" comes after "aqua".
"""
import math
import re
from colorsys import hls_to_rgb, rgb_to_hls
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Tuple, Union, cast

from pydantic.validators import not_none_validator

from .errors import ColorError
from .utils import almost_equal_floats

if TYPE_CHECKING:  # pragma: no cover
    from .types import CallableGenerator


RGBType = Tuple[int, int, int]
RGBAType = Tuple[int, int, int, float]
ColorType = Union[RGBType, RGBAType, str]
HSLType = Tuple[float, float, float]
HSLAType = Tuple[float, float, float, float]


class RGBA(NamedTuple):
    r: int
    g: int
    b: int
    alpha: Optional[float]


r_hex_short = re.compile(r'\s*(?:#|0x)?([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])?\s*')
r_hex_long = re.compile(r'\s*(?:#|0x)?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?\s*')
_r_255 = r'(\d{1,3}(?:\.\d+)?)'
_r_comma = r'\s*,\s*'
r_rgb = re.compile(fr'\s*rgb\(\s*{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_255}\)\s*')
_r_alpha = r'(\d(?:\.\d+)?|\.\d+|\d{1,2}%)'
r_rgba = re.compile(fr'\s*rgba\(\s*{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_alpha}\s*\)\s*')
_r_h = r'(-?\d+(?:\.\d+)?|-?\.\d+)(deg|rad|turn)?'
_r_sl = r'(\d{1,3}(?:\.\d+)?)%'
r_hsl = re.compile(fr'\s*hsl\(\s*{_r_h}{_r_comma}{_r_sl}{_r_comma}{_r_sl}\s*\)\s*')
r_hsla = re.compile(fr'\s*hsl\(\s*{_r_h}{_r_comma}{_r_sl}{_r_comma}{_r_sl}{_r_comma}{_r_alpha}\s*\)\s*')

# colors where the two hex characters are the same, if all colors match this the short version of hex colors can be used
repeat_colors = {int(c * 2, 16) for c in '0123456789abcdef'}
rads = 2 * math.pi


class Color:
    __slots__ = '_original', '_rgba'

    def __init__(self, value: ColorType) -> None:
        self._rgba: RGBA
        self._original: ColorType
        if isinstance(value, (tuple, list)):
            self._rgba = parse_tuple(value)
        elif isinstance(value, str):
            self._rgba = parse_str(value)
        else:
            raise ColorError(reason='value must be a tuple, list or string')

        # if we've got here value must be a valid color
        self._original = value

    def original(self) -> ColorType:
        """
        Original value passed to Color
        """
        return self._original

    def as_named(self, *, fallback: bool = False) -> str:
        if self._rgba.alpha is None:
            rgb = self._rgba.r, self._rgba.g, self._rgba.b
            try:
                return COLORS_BY_VALUE[rgb]
            except KeyError as e:
                if fallback:
                    return self.as_hex()
                else:
                    raise ValueError('no named color found, use fallback=True, as_hex() or as_rgb()') from e
        else:
            if fallback:
                return self.as_rgba()
            else:
                raise ValueError(
                    'a non-null alpha channel means named colors are not possible, use fallback=True or as_rgba()'
                )

    def as_hex(self, *, fallback: bool = False) -> str:
        if self._rgba.alpha is None:
            rgb = self.as_rgba_tuple(alpha=False)
            as_hex = '{:02x}{:02x}{:02x}'.format(*rgb)
            if all(c in repeat_colors for c in rgb):
                as_hex = as_hex[0] + as_hex[2] + as_hex[4]
            return '#' + as_hex
        else:
            if fallback:
                return self.as_rgba()
            else:
                raise ValueError(
                    'a non-null alpha channel means a hex color is not possible, use fallback=True or as_rgba()'
                )

    def as_rgba(self) -> str:
        return f'rgba({self._rgba.r}, {self._rgba.g}, {self._rgba.b}, {round(self._alpha_float(), 2)})'

    def as_rgb(self, *, fallback: bool = False) -> str:
        if self._rgba.alpha is None:
            return f'rgb({self._rgba.r}, {self._rgba.g}, {self._rgba.b})'
        else:
            if fallback:
                return self.as_rgba()
            else:
                raise ValueError(
                    'a non-null alpha channel means an rgb() color is not possible, use fallback=True or as_rgba()'
                )

    def as_rgba_tuple(self, *, alpha: Optional[bool] = True) -> Union[RGBType, RGBAType]:
        """
        Color as an RGB or RGBA tuple; red, green and blue are in the range 0 to 255, alpha if included is
        in the range 0 to 1.

        :param alpha: whether to include the alpha channel, options are
          True - (default) always include alpha,
          False - always omit alpha,
          None - include alpha only if it's set (e.g. not None)
        """
        r, g, b = self._rgba[:3]
        if alpha:
            # alpha is true
            return r, g, b, self._alpha_float()
        elif alpha is False:
            return r, g, b
        else:
            # alpha is None
            if self._rgba.alpha is None:
                return r, g, b
            else:
                return r, g, b, self._alpha_float()

    def as_hsla(self) -> str:
        h, s, li, a = self.as_hsla_tuple(alpha=True)  # type: ignore
        return f'hsla({h * 360:0.0f}, {s * 100:0.0f}%, {li * 100:0.0f}%, {round(a, 2)})'

    def as_hsl(self, *, fallback: bool = False) -> str:
        if self._rgba.alpha is None:
            h, s, li = self.as_hsla_tuple(alpha=False)  # type: ignore
            return f'hsl({h * 360:0.0f}, {s * 100:0.0f}%, {li * 100:0.0f}%)'
        else:
            if fallback:
                return self.as_hsla()
            else:
                raise ValueError(
                    'a non-null alpha channel means an hsl() color is not possible, use fallback=True or as_hsla()'
                )

    def as_hsla_tuple(self, *, alpha: Optional[bool] = True) -> Union[HSLType, HSLAType]:
        """
        Color as an HSL or HSLA tuple, e.g. hue, saturation, lightness and optionally alpha; all elements are in
        the range 0 to 1.

        NOTE: this is HSL as used in HTML and most other places, not HLS as used in python's colorsys.

        :param alpha: whether to include the alpha channel, options are
          True - (default) always include alpha,
          False - always omit alpha,
          None - include alpha only if it's set (e.g. not None)
        """
        h, l, s = rgb_to_hls(self._rgba.r / 255, self._rgba.g / 255, self._rgba.b / 255)
        if alpha:
            # alpha is true
            return h, s, l, self._alpha_float()
        elif alpha is False:
            return h, s, l
        else:
            # alpha is None
            if self._rgba.alpha is None:
                return h, s, l
            else:
                return h, s, l, self._alpha_float()

    def _alpha_float(self) -> float:
        return 1 if self._rgba.alpha is None else self._rgba.alpha

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield not_none_validator
        yield cls

    def __str__(self) -> str:
        return self.as_named(fallback=True)

    def __repr__(self) -> str:
        return f'<Color({str(self)!r}, {self.as_rgba_tuple(alpha=None)})>'


def parse_tuple(value: Tuple[Any, ...]) -> RGBA:
    """
    Parse a tuple or list as a color.
    """
    if len(value) == 3:
        r, g, b = [parse_int_color(v) for v in value]
        return RGBA(r, g, b, None)
    elif len(value) == 4:
        r, g, b = [parse_int_color(v) for v in value[:3]]
        return RGBA(r, g, b, parse_float_alpha(value[3]))
    else:
        raise ColorError(reason='tuples must have length 3 or 4')


def parse_str(value: str) -> RGBA:
    """
    Parse a string to an RGBA tuple, trying the following formats (in this order):
    * named color, see COLORS_BY_NAME below
    * hex short eg. `<prefix>fff` (prefix can be `#`, `0x` or nothing)
    * hex long eg. `<prefix>ffffff` (prefix can be `#`, `0x` or nothing)
    * `rgb(<r>, <g>, <b>) `
    * `rgba(<r>, <g>, <b>, <a>)`
    """
    value_lower = value.lower()
    try:
        r, g, b = COLORS_BY_NAME[value_lower]
    except KeyError:
        pass
    else:
        return RGBA(r, g, b, None)

    m = r_hex_short.fullmatch(value_lower)
    if m:
        *rgb, a = m.groups()
        r, g, b = [int(v * 2, 16) for v in rgb]
        if a:
            alpha: Optional[float] = int(a * 2, 16) / 255
        else:
            alpha = None
        return RGBA(r, g, b, alpha)

    m = r_hex_long.fullmatch(value_lower)
    if m:
        *rgb, a = m.groups()
        r, g, b = [int(v, 16) for v in rgb]
        if a:
            alpha = int(a, 16) / 255
        else:
            alpha = None
        return RGBA(r, g, b, cast(float, alpha))

    m = r_rgb.fullmatch(value_lower)
    if m:
        r, g, b = [parse_int_color(v) for v in m.groups()]
        return RGBA(r, g, b, None)

    m = r_rgba.fullmatch(value_lower)
    if m:
        r, g, b = [parse_int_color(v) for v in m.groups()[:3]]
        alpha = parse_float_alpha(m.group(4))
        return RGBA(r, g, b, alpha)

    m = r_hsl.fullmatch(value_lower)
    if m:
        h, h_units, s, l_ = m.groups()
        return parse_hsl(h, h_units, s, l_)

    m = r_hsla.fullmatch(value_lower)
    if m:
        h, h_units, s, l_, a = m.groups()
        return parse_hsl(h, h_units, s, l_, parse_float_alpha(a))

    raise ColorError(reason='string not recognised as a valid color')


def parse_int_color(value: Any, max: int = 255) -> int:
    """
    Parse a value checking it's a valid int in the range 0 to max
    """
    try:
        if isinstance(value, str) and '.' in value:
            # floats are allowed in rgb(a) colors
            # https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#RGB_transparency_variations
            value = float(value)
        color = int(value)
    except ValueError:
        raise ColorError(reason='color values must be a valid integer')
    if 0 <= color <= max:
        return color
    else:
        raise ColorError(reason=f'color values must be in the range 0 to {max}')


def parse_float_alpha(value: Any) -> Optional[float]:
    """
    Parse a value checking it's a valid float in the range 0 to 1
    """
    try:
        if isinstance(value, str) and value.endswith('%'):
            alpha = float(value[:-1]) / 100
        else:
            alpha = float(value)
    except ValueError:
        raise ColorError(reason='alpha values must be a valid float')

    if almost_equal_floats(alpha, 1):
        return None
    elif 0 <= alpha <= 1:
        return alpha
    else:
        raise ColorError(reason='alpha values must be in the range 0 to 1')


def parse_hsl(h: str, h_units: str, s: str, l: str, alpha: Optional[float] = None) -> RGBA:
    """
    Parse raw hue, saturation, lightness and alpha values and convert to RGBA.
    """
    s_value, l_value = parse_int_color(s, 100) / 100, parse_int_color(l, 100) / 100

    h_value = float(h)
    if h_units in {None, 'deg'}:
        h_value = h_value % 360 / 360
    elif h_units == 'rad':
        h_value = h_value % rads / rads
    else:
        # turns
        h_value = h_value % 1

    r, g, b = hls_to_rgb(h_value, l_value, s_value)
    return RGBA(float_to_255(r), float_to_255(g), float_to_255(b), alpha)


def float_to_255(v: float) -> int:
    return int(round(v * 255))


COLORS_BY_NAME = {
    'aliceblue': (240, 248, 255),
    'antiquewhite': (250, 235, 215),
    'aqua': (0, 255, 255),
    'aquamarine': (127, 255, 212),
    'azure': (240, 255, 255),
    'beige': (245, 245, 220),
    'bisque': (255, 228, 196),
    'black': (0, 0, 0),
    'blanchedalmond': (255, 235, 205),
    'blue': (0, 0, 255),
    'blueviolet': (138, 43, 226),
    'brown': (165, 42, 42),
    'burlywood': (222, 184, 135),
    'cadetblue': (95, 158, 160),
    'chartreuse': (127, 255, 0),
    'chocolate': (210, 105, 30),
    'coral': (255, 127, 80),
    'cornflowerblue': (100, 149, 237),
    'cornsilk': (255, 248, 220),
    'crimson': (220, 20, 60),
    'cyan': (0, 255, 255),
    'darkblue': (0, 0, 139),
    'darkcyan': (0, 139, 139),
    'darkgoldenrod': (184, 134, 11),
    'darkgray': (169, 169, 169),
    'darkgreen': (0, 100, 0),
    'darkgrey': (169, 169, 169),
    'darkkhaki': (189, 183, 107),
    'darkmagenta': (139, 0, 139),
    'darkolivegreen': (85, 107, 47),
    'darkorange': (255, 140, 0),
    'darkorchid': (153, 50, 204),
    'darkred': (139, 0, 0),
    'darksalmon': (233, 150, 122),
    'darkseagreen': (143, 188, 143),
    'darkslateblue': (72, 61, 139),
    'darkslategray': (47, 79, 79),
    'darkslategrey': (47, 79, 79),
    'darkturquoise': (0, 206, 209),
    'darkviolet': (148, 0, 211),
    'deeppink': (255, 20, 147),
    'deepskyblue': (0, 191, 255),
    'dimgray': (105, 105, 105),
    'dimgrey': (105, 105, 105),
    'dodgerblue': (30, 144, 255),
    'firebrick': (178, 34, 34),
    'floralwhite': (255, 250, 240),
    'forestgreen': (34, 139, 34),
    'fuchsia': (255, 0, 255),
    'gainsboro': (220, 220, 220),
    'ghostwhite': (248, 248, 255),
    'gold': (255, 215, 0),
    'goldenrod': (218, 165, 32),
    'gray': (128, 128, 128),
    'green': (0, 128, 0),
    'greenyellow': (173, 255, 47),
    'grey': (128, 128, 128),
    'honeydew': (240, 255, 240),
    'hotpink': (255, 105, 180),
    'indianred': (205, 92, 92),
    'indigo': (75, 0, 130),
    'ivory': (255, 255, 240),
    'khaki': (240, 230, 140),
    'lavender': (230, 230, 250),
    'lavenderblush': (255, 240, 245),
    'lawngreen': (124, 252, 0),
    'lemonchiffon': (255, 250, 205),
    'lightblue': (173, 216, 230),
    'lightcoral': (240, 128, 128),
    'lightcyan': (224, 255, 255),
    'lightgoldenrodyellow': (250, 250, 210),
    'lightgray': (211, 211, 211),
    'lightgreen': (144, 238, 144),
    'lightgrey': (211, 211, 211),
    'lightpink': (255, 182, 193),
    'lightsalmon': (255, 160, 122),
    'lightseagreen': (32, 178, 170),
    'lightskyblue': (135, 206, 250),
    'lightslategray': (119, 136, 153),
    'lightslategrey': (119, 136, 153),
    'lightsteelblue': (176, 196, 222),
    'lightyellow': (255, 255, 224),
    'lime': (0, 255, 0),
    'limegreen': (50, 205, 50),
    'linen': (250, 240, 230),
    'magenta': (255, 0, 255),
    'maroon': (128, 0, 0),
    'mediumaquamarine': (102, 205, 170),
    'mediumblue': (0, 0, 205),
    'mediumorchid': (186, 85, 211),
    'mediumpurple': (147, 112, 219),
    'mediumseagreen': (60, 179, 113),
    'mediumslateblue': (123, 104, 238),
    'mediumspringgreen': (0, 250, 154),
    'mediumturquoise': (72, 209, 204),
    'mediumvioletred': (199, 21, 133),
    'midnightblue': (25, 25, 112),
    'mintcream': (245, 255, 250),
    'mistyrose': (255, 228, 225),
    'moccasin': (255, 228, 181),
    'navajowhite': (255, 222, 173),
    'navy': (0, 0, 128),
    'oldlace': (253, 245, 230),
    'olive': (128, 128, 0),
    'olivedrab': (107, 142, 35),
    'orange': (255, 165, 0),
    'orangered': (255, 69, 0),
    'orchid': (218, 112, 214),
    'palegoldenrod': (238, 232, 170),
    'palegreen': (152, 251, 152),
    'paleturquoise': (175, 238, 238),
    'palevioletred': (219, 112, 147),
    'papayawhip': (255, 239, 213),
    'peachpuff': (255, 218, 185),
    'peru': (205, 133, 63),
    'pink': (255, 192, 203),
    'plum': (221, 160, 221),
    'powderblue': (176, 224, 230),
    'purple': (128, 0, 128),
    'red': (255, 0, 0),
    'rosybrown': (188, 143, 143),
    'royalblue': (65, 105, 225),
    'saddlebrown': (139, 69, 19),
    'salmon': (250, 128, 114),
    'sandybrown': (244, 164, 96),
    'seagreen': (46, 139, 87),
    'seashell': (255, 245, 238),
    'sienna': (160, 82, 45),
    'silver': (192, 192, 192),
    'skyblue': (135, 206, 235),
    'slateblue': (106, 90, 205),
    'slategray': (112, 128, 144),
    'slategrey': (112, 128, 144),
    'snow': (255, 250, 250),
    'springgreen': (0, 255, 127),
    'steelblue': (70, 130, 180),
    'tan': (210, 180, 140),
    'teal': (0, 128, 128),
    'thistle': (216, 191, 216),
    'tomato': (255, 99, 71),
    'turquoise': (64, 224, 208),
    'violet': (238, 130, 238),
    'wheat': (245, 222, 179),
    'white': (255, 255, 255),
    'whitesmoke': (245, 245, 245),
    'yellow': (255, 255, 0),
    'yellowgreen': (154, 205, 50),
}

COLORS_BY_VALUE = {v: k for k, v in COLORS_BY_NAME.items()}
