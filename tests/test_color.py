from datetime import datetime

import pytest

from pydantic import BaseModel, ValidationError
from pydantic.color import Color
from pydantic.errors import ColorError
from pydantic.utils import almost_equal_floats


@pytest.mark.parametrize(
    'raw_color, as_tuple',
    [
        # named colors
        ('aliceblue', (240, 248, 255)),
        ('Antiquewhite', (250, 235, 215)),
        ('#000000', (0, 0, 0)),
        ('#DAB', (221, 170, 187)),
        ('#dab', (221, 170, 187)),
        ('#000', (0, 0, 0)),
        ('0x797979', (121, 121, 121)),
        ('0x777', (119, 119, 119)),
        ('0x777777', (119, 119, 119)),
        ('777', (119, 119, 119)),
        (' 777', (119, 119, 119)),
        ('777 ', (119, 119, 119)),
        (' 777 ', (119, 119, 119)),
        ((0, 0, 128), (0, 0, 128)),
        ([0, 0, 128], (0, 0, 128)),
        ((0, 0, 205, 1.0), (0, 0, 205)),
        ((0, 0, 205, 0.5), (0, 0, 205, 0.5)),
        ('rgb(0, 0, 205)', (0, 0, 205)),
        ('rgba(0, 0, 128, 0.6)', (0, 0, 128, 0.6)),
        (' rgba(0, 0, 128,0.6) ', (0, 0, 128, 0.6)),
        ('rgba(00,0,128,0.6  )', (0, 0, 128, 0.6)),
        ('rgba(0, 0, 128, 0)', (0, 0, 128, 0)),
        ('rgba(0, 0, 128, 1)', (0, 0, 128)),
    ],
)
def test_color_success(raw_color, as_tuple):
    c = Color(raw_color)
    assert c.as_rgba_tuple(alpha=None) == as_tuple
    assert c.original() == raw_color


@pytest.mark.parametrize(
    'color',
    [
        # named colors
        'nosuchname',
        'chucknorris',
        # hex
        '#0000000',
        '#0000',
        'x000',
        # rgb/rgba tuples
        (256, 256, 256),
        (128, 128, 128, 0.5, 128),
        (0, 0, 'x'),
        (0, 0, 0, 1.5),
        (0, 0, 0, 'x'),
        (0, 0, 1280),
        (0, 0, 1205, 0.1),
        (0, 0, 1128, 0.5),
        (0, 0, 1128, -0.5),
        (0, 0, 1128, 1.5),
        # rgb/rgba strings
        'rgb(0, 0, 1205)',
        'rgb(0, 0, 1128)',
        'rgba(0, 0, 11205, 0.1)',
        'rgba(0, 0, 128, 11.5)',
        # neither a tuple, not a string
        datetime(2017, 10, 5, 19, 47, 7),
        object,
        range(10),
    ],
)
def test_color_fail(color):
    with pytest.raises(ColorError):
        Color(color)


def test_model_validation():
    class Model(BaseModel):
        color: Color

    assert Model(color='red').color.as_hex() == '#f00'
    with pytest.raises(ValidationError) as exc_info:
        Model(color='snot')
    assert exc_info.value.errors() == [
        {
            'loc': ('color',),
            'msg': 'value is not a valid color: string not recognised as a valid color',
            'type': 'value_error.color',
            'ctx': {'reason': 'string not recognised as a valid color'},
        }
    ]


def test_as_rgba():
    assert Color('bad').as_rgba() == 'rgba(187, 170, 221, 1)'
    assert Color((1, 2, 3, 0.123456)).as_rgba() == 'rgba(1, 2, 3, 0.12)'


def test_as_rgb():
    assert Color('bad').as_rgb() == 'rgb(187, 170, 221)'
    with pytest.raises(ValueError) as exc_info:
        Color((1, 2, 3, 0.123456)).as_rgb()
    assert exc_info.value.args[0] == (
        'a non-null alpha channel means an rgb() color is not possible, use fallback=True or as_rgba()'
    )
    assert Color((1, 2, 3, 0.1)).as_rgb(fallback=True) == 'rgba(1, 2, 3, 0.1)'


def test_as_rgba_tuple():
    assert Color((1, 2, 3)).as_rgba_tuple(alpha=None) == (1, 2, 3)
    assert Color((1, 2, 3, 1)).as_rgba_tuple(alpha=None) == (1, 2, 3)
    assert Color((1, 2, 3, 0.3)).as_rgba_tuple(alpha=None) == (1, 2, 3, 0.3)
    assert Color((1, 2, 3, 0.3)).as_rgba_tuple(alpha=None) == (1, 2, 3, 0.3)

    assert Color((1, 2, 3)).as_rgba_tuple(alpha=False) == (1, 2, 3)
    assert Color((1, 2, 3, 0.3)).as_rgba_tuple(alpha=False) == (1, 2, 3)

    assert Color((1, 2, 3)).as_rgba_tuple() == (1, 2, 3, 1)
    assert Color((1, 2, 3, 0.3)).as_rgba_tuple() == (1, 2, 3, 0.3)


def test_as_hsla():
    assert Color('bad').as_hsla() == 'hsla(260, 43%, 77%, 1)'
    assert Color((1, 2, 3, 0.123456)).as_hsla() == 'hsla(210, 50%, 1%, 0.12)'


def test_as_hsl():
    assert Color('bad').as_hsl() == 'hsl(260, 43%, 77%)'
    with pytest.raises(ValueError) as exc_info:
        Color((1, 2, 3, 0.123456)).as_hsl()
    assert exc_info.value.args[0] == (
        'a non-null alpha channel means an hsl() color is not possible, use fallback=True or as_hsla()'
    )
    assert Color((1, 2, 3, 0.123456)).as_hsl(fallback=True) == 'hsla(210, 50%, 1%, 0.12)'


def test_as_hsla_tuple():
    c = Color('016997')
    h, s, l, a = c.as_hsla_tuple()
    assert almost_equal_floats(h, 0.551, delta=0.01)
    assert almost_equal_floats(s, 0.986, delta=0.01)
    assert almost_equal_floats(l, 0.298, delta=0.01)
    assert a == 1

    assert c.as_hsla_tuple(alpha=False) == c.as_hsla_tuple(alpha=None) == (h, s, l)

    c = Color((3, 40, 50, 0.5))
    hsla = c.as_hsla_tuple(alpha=None)
    assert len(hsla) == 4
    assert hsla[3] == 0.5


def test_as_hex():
    assert Color((1, 2, 3)).as_hex() == '#010203'
    assert Color((119, 119, 119)).as_hex() == '#777'
    assert Color((119, 0, 238)).as_hex() == '#70e'
    assert Color('B0B').as_hex() == '#b0b'
    with pytest.raises(ValueError) as exc_info:
        Color((1, 2, 3, 0.123456)).as_hex()
    assert exc_info.value.args[0] == (
        'a non-null alpha channel means a hex color is not possible, use fallback=True or as_rgba()'
    )
    assert Color((1, 2, 3, 0.1)).as_hex(fallback=True) == 'rgba(1, 2, 3, 0.1)'
    assert Color((119, 119, 119, 0.1)).as_hex(fallback=True) == 'rgba(119, 119, 119, 0.1)'


def test_as_named():
    assert Color((0, 255, 255)).as_named() == 'cyan'
    assert Color('#808000').as_named() == 'olive'

    assert Color((240, 248, 255)).as_named() == 'aliceblue'
    with pytest.raises(ValueError) as exc_info:
        Color((1, 2, 3)).as_named()
    assert exc_info.value.args[0] == 'no named color found, use fallback=True, as_hex() or as_rgb()'
    with pytest.raises(ValueError) as exc_info:
        Color((1, 2, 3, 0.1)).as_named()
    assert exc_info.value.args[0] == (
        'a non-null alpha channel means named colors are not possible, use fallback=True or as_rgba()'
    )
    assert Color((1, 2, 3)).as_named(fallback=True) == '#010203'
    assert Color((1, 2, 3, 0.1)).as_named(fallback=True) == 'rgba(1, 2, 3, 0.1)'


def test_str_repr():
    assert str(Color('red')) == 'red'
    assert repr(Color('red')) == "<Color('red', (255, 0, 0))>"
    assert str(Color((1, 2, 3))) == '#010203'
    assert repr(Color((1, 2, 3))) == "<Color('#010203', (1, 2, 3))>"
