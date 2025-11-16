from datetime import datetime

import pytest
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, ValidationError
from pydantic.color import Color

pytestmark = pytest.mark.filterwarnings(
    'ignore:The `Color` class is deprecated, use `pydantic_extra_types` instead.*:DeprecationWarning'
)


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
        ('0x777777cc', (119, 119, 119, 0.8)),
        ('777', (119, 119, 119)),
        ('777c', (119, 119, 119, 0.8)),
        (' 777', (119, 119, 119)),
        ('777 ', (119, 119, 119)),
        (' 777 ', (119, 119, 119)),
        ((0, 0, 128), (0, 0, 128)),
        ([0, 0, 128], (0, 0, 128)),
        ((0, 0, 205, 1.0), (0, 0, 205)),
        ((0, 0, 205, 0.5), (0, 0, 205, 0.5)),
        ('rgb(0, 0, 205)', (0, 0, 205)),
        ('rgb(0, 0, 205.2)', (0, 0, 205)),
        ('rgb(0, 0.2, 205)', (0, 0, 205)),
        ('rgba(0, 0, 128, 0.6)', (0, 0, 128, 0.6)),
        ('rgba(0, 0, 128, .6)', (0, 0, 128, 0.6)),
        ('rgba(0, 0, 128, 60%)', (0, 0, 128, 0.6)),
        (' rgba(0, 0, 128,0.6) ', (0, 0, 128, 0.6)),
        ('rgba(00,0,128,0.6  )', (0, 0, 128, 0.6)),
        ('rgba(0, 0, 128, 0)', (0, 0, 128, 0)),
        ('rgba(0, 0, 128, 1)', (0, 0, 128)),
        ('rgb(0 0.2 205)', (0, 0, 205)),
        ('rgb(0 0.2 205 / 0.6)', (0, 0, 205, 0.6)),
        ('rgb(0 0.2 205 / 60%)', (0, 0, 205, 0.6)),
        ('rgba(0 0 128)', (0, 0, 128)),
        ('rgba(0 0 128 / 0.6)', (0, 0, 128, 0.6)),
        ('rgba(0 0 128 / 60%)', (0, 0, 128, 0.6)),
        ('hsl(270, 60%, 70%)', (178, 133, 224)),
        ('hsl(180, 100%, 50%)', (0, 255, 255)),
        ('hsl(630, 60%, 70%)', (178, 133, 224)),
        ('hsl(270deg, 60%, 70%)', (178, 133, 224)),
        ('hsl(.75turn, 60%, 70%)', (178, 133, 224)),
        ('hsl(-.25turn, 60%, 70%)', (178, 133, 224)),
        ('hsl(-0.25turn, 60%, 70%)', (178, 133, 224)),
        ('hsl(4.71238rad, 60%, 70%)', (178, 133, 224)),
        ('hsl(10.9955rad, 60%, 70%)', (178, 133, 224)),
        ('hsl(270, 60%, 50%, .15)', (127, 51, 204, 0.15)),
        ('hsl(270.00deg, 60%, 50%, 15%)', (127, 51, 204, 0.15)),
        ('hsl(630 60% 70%)', (178, 133, 224)),
        ('hsl(270 60% 50% / .15)', (127, 51, 204, 0.15)),
        ('hsla(630, 60%, 70%)', (178, 133, 224)),
        ('hsla(630 60% 70%)', (178, 133, 224)),
        ('hsla(270 60% 50% / .15)', (127, 51, 204, 0.15)),
    ],
)
def test_color_success(raw_color, as_tuple):
    c = Color(raw_color)
    assert c.as_rgb_tuple() == as_tuple
    assert c.original() == raw_color


@pytest.mark.parametrize(
    'color',
    [
        # named colors
        'nosuchname',
        'chucknorris',
        # hex
        '#0000000',
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
        'rgb(0, 0, 200 / 0.2)',
        'rgb(72 122 18, 0.3)',
        'rgba(0, 0, 11205, 0.1)',
        'rgba(0, 0, 128, 11.5)',
        'rgba(0, 0, 128 / 11.5)',
        'rgba(72 122 18 0.3)',
        # hsl/hsla strings
        'hsl(180, 101%, 50%)',
        'hsl(72 122 18 / 0.3)',
        'hsl(630 60% 70%, 0.3)',
        'hsla(72 122 18 / 0.3)',
        # neither a tuple, not a string
        datetime(2017, 10, 5, 19, 47, 7),
        object,
        range(10),
    ],
)
def test_color_fail(color):
    with pytest.raises(PydanticCustomError) as exc_info:
        Color(color)
    assert exc_info.value.type == 'color_error'


def test_model_validation():
    class Model(BaseModel):
        color: Color

    assert Model(color='red').color.as_hex() == '#f00'
    assert Model(color=Color('red')).color.as_hex() == '#f00'
    with pytest.raises(ValidationError) as exc_info:
        Model(color='snot')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'color_error',
            'loc': ('color',),
            'msg': 'value is not a valid color: string not recognised as a valid color',
            'input': 'snot',
        }
    ]


def test_as_rgb():
    assert Color('bad').as_rgb() == 'rgb(187, 170, 221)'
    assert Color((1, 2, 3, 0.123456)).as_rgb() == 'rgba(1, 2, 3, 0.12)'
    assert Color((1, 2, 3, 0.1)).as_rgb() == 'rgba(1, 2, 3, 0.1)'


def test_as_rgb_tuple():
    assert Color((1, 2, 3)).as_rgb_tuple(alpha=None) == (1, 2, 3)
    assert Color((1, 2, 3, 1)).as_rgb_tuple(alpha=None) == (1, 2, 3)
    assert Color((1, 2, 3, 0.3)).as_rgb_tuple(alpha=None) == (1, 2, 3, 0.3)
    assert Color((1, 2, 3, 0.3)).as_rgb_tuple(alpha=None) == (1, 2, 3, 0.3)

    assert Color((1, 2, 3)).as_rgb_tuple(alpha=False) == (1, 2, 3)
    assert Color((1, 2, 3, 0.3)).as_rgb_tuple(alpha=False) == (1, 2, 3)

    assert Color((1, 2, 3)).as_rgb_tuple(alpha=True) == (1, 2, 3, 1)
    assert Color((1, 2, 3, 0.3)).as_rgb_tuple(alpha=True) == (1, 2, 3, 0.3)


def test_as_hsl():
    assert Color('bad').as_hsl() == 'hsl(260, 43%, 77%)'
    assert Color((1, 2, 3, 0.123456)).as_hsl() == 'hsl(210, 50%, 1%, 0.12)'
    assert Color('hsl(260, 43%, 77%)').as_hsl() == 'hsl(260, 43%, 77%)'


def test_as_hsl_tuple():
    c = Color('016997')
    h, s, l_, a = c.as_hsl_tuple(alpha=True)
    assert h == pytest.approx(0.551, rel=0.01)
    assert s == pytest.approx(0.986, rel=0.01)
    assert l_ == pytest.approx(0.298, rel=0.01)
    assert a == 1

    assert c.as_hsl_tuple(alpha=False) == c.as_hsl_tuple(alpha=None) == (h, s, l_)

    c = Color((3, 40, 50, 0.5))
    hsla = c.as_hsl_tuple(alpha=None)
    assert len(hsla) == 4
    assert hsla[3] == 0.5


def test_as_hex():
    assert Color((1, 2, 3)).as_hex() == '#010203'
    assert Color((119, 119, 119)).as_hex() == '#777'
    assert Color((119, 0, 238)).as_hex() == '#70e'
    assert Color('B0B').as_hex() == '#b0b'
    assert Color((1, 2, 3, 0.123456)).as_hex() == '#0102031f'
    assert Color((1, 2, 3, 0.1)).as_hex() == '#0102031a'


def test_as_named():
    assert Color((0, 255, 255)).as_named() == 'cyan'
    assert Color('#808000').as_named() == 'olive'
    assert Color('hsl(180, 100%, 50%)').as_named() == 'cyan'

    assert Color((240, 248, 255)).as_named() == 'aliceblue'
    with pytest.raises(ValueError) as exc_info:
        Color((1, 2, 3)).as_named()
    assert exc_info.value.args[0] == 'no named color found, use fallback=True, as_hex() or as_rgb()'

    assert Color((1, 2, 3)).as_named(fallback=True) == '#010203'
    assert Color((1, 2, 3, 0.1)).as_named(fallback=True) == '#0102031a'


def test_str_repr():
    assert str(Color('red')) == 'red'
    assert repr(Color('red')) == "Color('red', rgb=(255, 0, 0))"
    assert str(Color((1, 2, 3))) == '#010203'
    assert repr(Color((1, 2, 3))) == "Color('#010203', rgb=(1, 2, 3))"


def test_eq():
    assert Color('red') == Color('red')
    assert Color('red') != Color('blue')
    assert Color('red') != 'red'

    assert Color('red') == Color((255, 0, 0))
    assert Color('red') != Color((0, 0, 255))


def test_color_hashable():
    assert hash(Color('red')) != hash(Color('blue'))
    assert hash(Color('red')) == hash(Color((255, 0, 0)))
    assert hash(Color('red')) != hash(Color((255, 0, 0, 0.5)))
