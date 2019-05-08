"""
Color definitions are  used as per CSS3 specification:
http://www.w3.org/TR/css3-color/#svg-color

In turn CSS3 is based on SVG specification for color names:
http://www.w3.org/TR/SVG11/types.html#ColorKeywords

Watch out! A few named colors have the same hex/rgb codes. This usually applies to the shades of gray because of
the variations in spelling, e.g. `slategrey` and `slategray`.

A few colors have completely different names but the same hex/rgb though, e.g. `aqua` and `cyan`.  A complete
list of non-unique colors in hex format: ['00ffff', '2f4f4f', '696969', '708090', '778899', '808080', 'a9a9a9',
'd3d3d3', 'ff00ff']. Because of this overlap only one named colour with non-unique hex/rgb will be represented in
"""

import re
from colorsys import rgb_to_hls
from typing import TYPE_CHECKING, Any, Generator, Optional, Tuple, Type, Union

from . import errors
from .utils import almost_equal_floats

if TYPE_CHECKING:  # pragma: no cover
    from .dataclasses import DataclassType  # noqa: F401
    from .main import BaseModel  # noqa: F401
    from .utils import AnyCallable

    CallableGenerator = Generator[AnyCallable, None, None]
    ModelOrDc = Type[Union['BaseModel', 'DataclassType']]


RGBType = Tuple[int, int, int]
RGBAType = Tuple[int, int, int, float]
AnyRGBType = Union[RGBType, RGBAType]
RGBFractionType = Tuple[float, float, float]
HLSType = Tuple[float, float, float]
ColorType = Union[str, AnyRGBType]

#
# Mappings
#

BY_NAME = {
    'aliceblue': 'f0f8ff',
    'antiquewhite': 'faebd7',
    'aqua': '00ffff',
    'aquamarine': '7fffd4',
    'azure': 'f0ffff',
    'beige': 'f5f5dc',
    'bisque': 'ffe4c4',
    'black': '000000',
    'blanchedalmond': 'ffebcd',
    'blue': '0000ff',
    'blueviolet': '8a2be2',
    'brown': 'a52a2a',
    'burlywood': 'deb887',
    'cadetblue': '5f9ea0',
    'chartreuse': '7fff00',
    'chocolate': 'd2691e',
    'coral': 'ff7f50',
    'cornflowerblue': '6495ed',
    'cornsilk': 'fff8dc',
    'crimson': 'dc143c',
    'cyan': '00ffff',
    'darkblue': '00008b',
    'darkcyan': '008b8b',
    'darkgoldenrod': 'b8860b',
    'darkgray': 'a9a9a9',
    'darkgreen': '006400',
    'darkgrey': 'a9a9a9',
    'darkkhaki': 'bdb76b',
    'darkmagenta': '8b008b',
    'darkolivegreen': '556b2f',
    'darkorange': 'ff8c00',
    'darkorchid': '9932cc',
    'darkred': '8b0000',
    'darksalmon': 'e9967a',
    'darkseagreen': '8fbc8f',
    'darkslateblue': '483d8b',
    'darkslategray': '2f4f4f',
    'darkslategrey': '2f4f4f',
    'darkturquoise': '00ced1',
    'darkviolet': '9400d3',
    'deeppink': 'ff1493',
    'deepskyblue': '00bfff',
    'dimgray': '696969',
    'dimgrey': '696969',
    'dodgerblue': '1e90ff',
    'firebrick': 'b22222',
    'floralwhite': 'fffaf0',
    'forestgreen': '228b22',
    'fuchsia': 'ff00ff',
    'gainsboro': 'dcdcdc',
    'ghostwhite': 'f8f8ff',
    'gold': 'ffd700',
    'goldenrod': 'daa520',
    'gray': '808080',
    'green': '008000',
    'greenyellow': 'adff2f',
    'grey': '808080',
    'honeydew': 'f0fff0',
    'hotpink': 'ff69b4',
    'indianred': 'cd5c5c',
    'indigo': '4b0082',
    'ivory': 'fffff0',
    'khaki': 'f0e68c',
    'lavender': 'e6e6fa',
    'lavenderblush': 'fff0f5',
    'lawngreen': '7cfc00',
    'lemonchiffon': 'fffacd',
    'lightblue': 'add8e6',
    'lightcoral': 'f08080',
    'lightcyan': 'e0ffff',
    'lightgoldenrodyellow': 'fafad2',
    'lightgray': 'd3d3d3',
    'lightgreen': '90ee90',
    'lightgrey': 'd3d3d3',
    'lightpink': 'ffb6c1',
    'lightsalmon': 'ffa07a',
    'lightseagreen': '20b2aa',
    'lightskyblue': '87cefa',
    'lightslategray': '778899',
    'lightslategrey': '778899',
    'lightsteelblue': 'b0c4de',
    'lightyellow': 'ffffe0',
    'lime': '00ff00',
    'limegreen': '32cd32',
    'linen': 'faf0e6',
    'magenta': 'ff00ff',
    'maroon': '800000',
    'mediumaquamarine': '66cdaa',
    'mediumblue': '0000cd',
    'mediumorchid': 'ba55d3',
    'mediumpurple': '9370db',
    'mediumseagreen': '3cb371',
    'mediumslateblue': '7b68ee',
    'mediumspringgreen': '00fa9a',
    'mediumturquoise': '48d1cc',
    'mediumvioletred': 'c71585',
    'midnightblue': '191970',
    'mintcream': 'f5fffa',
    'mistyrose': 'ffe4e1',
    'moccasin': 'ffe4b5',
    'navajowhite': 'ffdead',
    'navy': '000080',
    'oldlace': 'fdf5e6',
    'olive': '808000',
    'olivedrab': '6b8e23',
    'orange': 'ffa500',
    'orangered': 'ff4500',
    'orchid': 'da70d6',
    'palegoldenrod': 'eee8aa',
    'palegreen': '98fb98',
    'paleturquoise': 'afeeee',
    'palevioletred': 'db7093',
    'papayawhip': 'ffefd5',
    'peachpuff': 'ffdab9',
    'peru': 'cd853f',
    'pink': 'ffc0cb',
    'plum': 'dda0dd',
    'powderblue': 'b0e0e6',
    'purple': '800080',
    'red': 'ff0000',
    'rosybrown': 'bc8f8f',
    'royalblue': '4169e1',
    'saddlebrown': '8b4513',
    'salmon': 'fa8072',
    'sandybrown': 'f4a460',
    'seagreen': '2e8b57',
    'seashell': 'fff5ee',
    'sienna': 'a0522d',
    'silver': 'c0c0c0',
    'skyblue': '87ceeb',
    'slateblue': '6a5acd',
    'slategray': '708090',
    'slategrey': '708090',
    'snow': 'fffafa',
    'springgreen': '00ff7f',
    'steelblue': '4682b4',
    'tan': 'd2b48c',
    'teal': '008080',
    'thistle': 'd8bfd8',
    'tomato': 'ff6347',
    'turquoise': '40e0d0',
    'violet': 'ee82ee',
    'wheat': 'f5deb3',
    'white': 'ffffff',
    'whitesmoke': 'f5f5f5',
    'yellow': 'ffff00',
    'yellowgreen': '9acd32',
}


BY_HEX = {v: k for k, v in BY_NAME.items()}


#
# Color Type
#


class Color:
    __slots__ = '_original', '_color_match'

    def __init__(self, value: ColorType) -> None:
        self._original: ColorType = value
        self._color_match: Optional[str] = None
        self._parse_color()

    def original(self) -> ColorType:
        """
        Return original value passed to the model
        """
        return self._original

    def as_hex(self, prefix: str = '0x', reduce: bool = True) -> str:
        """
        Return hexadecimal value of the color

        Try reduce hex code to 3-digit format, fallback to 6-digit.
        """
        h = BY_NAME[self._color_match]  # type: ignore
        return '{}{}'.format(prefix, self._reduce_6_digit_hex(h) if reduce else h)

    def as_tuple(self, alpha: bool = False) -> AnyRGBType:
        """
        Return RGB or RGBA tuple
        """
        r, g, b = self._hex_to_rgb(BY_NAME[self._color_match])  # type: ignore

        if alpha:
            return r, g, b, 1.0
        return r, g, b

    def as_rgb(self, alpha: bool = False) -> str:
        """
        Return RGB or RGBA string representation of the color
        """
        rgb = self.as_tuple(alpha)
        if alpha:
            return 'rgba({}, {}, {}, {})'.format(*rgb[:3], round(rgb[-1], 2))
        return 'rgb({}, {}, {})'.format(*rgb)

    def as_named_color(self) -> str:
        """
        Return name of the color as per CSS3 specification.
        """
        return self._color_match  # type: ignore

    def as_hls(self) -> HLSType:
        """
        Return tuple of floats representing Hue Lightness Saturation (HLS) color
        """

        def normalize(v: Union[int, float, str]) -> float:
            return float(v) / 255

        r, g, b = self.as_tuple(alpha=False)  # type: ignore
        return rgb_to_hls(normalize(r), normalize(g), normalize(b))

    @classmethod
    def validate(cls, value: ColorType) -> 'Color':
        color = cls(value)
        color._get_color_or_raise()
        return color

    @staticmethod
    def _rgb_str_to_tuple(value: str) -> Optional[RGBAType]:
        """
        Return RGB/RGBA tuple from the passed string.

        If RGBA cannot be matched, return None
        """
        r = re.compile(
            r'rgba?\((?P<red>\d{1,3}),\s*'
            r'(?P<green>\d{1,3}),\s*'
            r'(?P<blue>\d{1,3})'
            r'(,\s*(?P<alpha>\d{1}\.\d+))?\)',
            re.IGNORECASE,
        )
        match = r.match(value)

        if match is None:
            return None

        red = int(match.group('red'))
        green = int(match.group('green'))
        blue = int(match.group('blue'))
        alpha = float(match.group('alpha')) if match.group('alpha') is not None else 1.0
        return red, green, blue, alpha

    @staticmethod
    def _is_int_color(value: Any) -> bool:
        """
        Return True if value can be converted to int in range [0, 256)
        """
        try:
            color = int(value)
        except ValueError:
            return False
        return color in range(0, 256)

    @staticmethod
    def _tuple_to_rgb(value: Optional[Tuple[Any, ...]]) -> Optional[RGBType]:
        """
        Convert an arbitrary tuple to RGB tuple of ints

        If conversion is not possible return None
        """
        if (value is None) or (len(value) not in range(3, 5)):
            return None

        if len(value) == 4:
            try:
                almost_equal_floats(float(value[3]), 1.0)
            except ValueError:
                return None

        if any(not Color._is_int_color(c) for c in value):
            return None

        r, g, b = value[:3]
        return r, g, b

    def _parse_tuple(self, value: Optional[Tuple[Any, ...]]) -> Optional[str]:
        """
        Get name of the color by its RGB
        """
        rgb = self._tuple_to_rgb(value)
        h = self._rgb_to_hex(rgb)
        return BY_HEX.get(h)  # type: ignore

    def _expand_3_digit_hex(self, value: Optional[str]) -> Optional[str]:
        """
        Return 6-digit hexadecimal value from the 3-digit format, fallback to original value
        """
        if (value is None) or (len(value) != 3):
            return value
        return '{0}{0}{1}{1}{2}{2}'.format(*value)

    def _reduce_6_digit_hex(self, value: str) -> str:
        """
        Return 3-digit hexadecimal value from 6-digit, fallback to original value
        """
        if len(value) != 6:
            return value
        a, b, c, d, e, f = value
        return '{a}{c}{e}'.format(a=a, c=c, e=e) if (a == b and c == d and e == f) else value

    def _hex_to_rgb(self, value: str) -> RGBType:
        """
        Convert a hexadecimal string to RGB tuple
        """
        h = self._expand_3_digit_hex(self._strip_hex(value))
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)  # type: ignore

    def _rgb_to_hex(self, value: Optional[RGBType]) -> Optional[str]:
        """
        Convert an RGB tuple to a 6-digit hexadecimal string
        """
        if value is None:
            return None
        t = tuple(map(lambda c: self._strip_hex(hex(c)).zfill(2), value))
        return "{}{}{}".format(*t)

    def _strip_hex(self, value: str) -> str:
        """
        Strip leading characters representing a hex string
        """
        if value.startswith('#'):
            return value[1:]
        elif value.startswith('0x'):
            return value[2:]
        return value

    def _parse_rgb_str(self, value: str) -> Optional[str]:
        """
        Get name of the color by its RGB/RGBA string
        """
        rgba = self._rgb_str_to_tuple(value)
        return self._parse_tuple(rgba)

    def _parse_hex_str(self, value: str) -> Optional[str]:
        """
        Get name of the color by its hexadecimal string
        """
        h = self._strip_hex(value)

        if len(h) == 3:
            h = self._expand_3_digit_hex(h)  # type: ignore

        return BY_HEX.get(h)

    def _parse_color(self) -> None:
        """
        Main logic of color parsing
        """
        if isinstance(self._original, tuple):
            self._color_match = self._parse_tuple(self._original)

        elif isinstance(self._original, str):
            color = self._original.lower()

            # rgb/rgba string
            self._color_match = self._parse_rgb_str(color)
            if self._color_match is not None:
                return

            # hex string
            self._color_match = self._parse_hex_str(color)
            if self._color_match is not None:
                return

            # named colour
            if color in BY_NAME:
                self._color_match = color
                return

    def _get_color_or_raise(self) -> None:
        """
        Raise error if color name not found
        """
        if self._color_match is None:
            raise errors.ColorError()

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    def __str__(self) -> str:
        return str(self._original).lower()

    def __repr__(self) -> str:
        return '<Color("{}")>'.format(self._color_match or self._original)
