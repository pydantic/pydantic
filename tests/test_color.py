from datetime import datetime

import pytest

from pydantic import BaseModel, ValidationError
from pydantic.color import Color
from pydantic.utils import almost_equal_floats


@pytest.mark.parametrize(
    'color, as_name, as_tuple, as_hex, as_hls',
    [
        # named colors
        ('aliceblue', 'aliceblue', (240, 248, 255), 'f0f8ff', (0.5777777777777778, 0.9705882352941176, 1.0)),
        (
            'Antiquewhite',
            'antiquewhite',
            (250, 235, 215),
            'faebd7',
            (0.09523809523809519, 0.9117647058823529, 0.7777777777777779),
        ),
        ('AQUA', 'aqua', (0, 255, 255), '0ff', (0.5, 0.5, 1.0)),
        ('aquaMarine', 'aquamarine', (127, 255, 212), '7fffd4', (0.4440104166666667, 0.7490196078431373, 1.0)),
        # hex: 6-digit and 3-digit
        ('#000000', 'black', (0, 0, 0), '000', (0.0, 0.0, 0.0)),
        ('#000', 'black', (0, 0, 0), '000', (0.0, 0.0, 0.0)),
        ('0x000080', 'navy', (0, 0, 128), '000080', (0.6666666666666666, 0.25098039215686274, 1.0)),
        ('0x00F', 'blue', (0, 0, 255), '00f', (0.6666666666666666, 0.5, 1.0)),
        ('000000', 'black', (0, 0, 0), '000', (0.0, 0.0, 0.0)),
        ('000', 'black', (0, 0, 0), '000', (0.0, 0.0, 0.0)),
        # rgb/rgba tuples
        ((0, 0, 0), 'black', (0, 0, 0), '000', (0.0, 0.0, 0.0)),
        ((0, 0, 128), 'navy', (0, 0, 128), '000080', (0.6666666666666666, 0.25098039215686274, 1.0)),
        ((0, 0, 205, 1.0), 'mediumblue', (0, 0, 205), '0000cd', (0.6666666666666666, 0.4019607843137255, 1.0)),
        ((0, 0, 128, 1.0), 'navy', (0, 0, 128), '000080', (0.6666666666666666, 0.25098039215686274, 1.0)),
        # rgb/rgba strings
        ('rgb(0, 0, 205)', 'mediumblue', (0, 0, 205), '0000cd', (0.6666666666666666, 0.4019607843137255, 1.0)),
        ('rgb(0, 0, 128)', 'navy', (0, 0, 128), '000080', (0.6666666666666666, 0.25098039215686274, 1.0)),
        ('rgba(0, 0, 205, 1.0)', 'mediumblue', (0, 0, 205), '0000cd', (0.6666666666666666, 0.4019607843137255, 1.0)),
        ('rgba(0, 0, 128, 1.0)', 'navy', (0, 0, 128), '000080', (0.6666666666666666, 0.25098039215686274, 1.0)),
    ],
)
def test_color_success(color, as_name, as_tuple, as_hex, as_hls):
    class Model(BaseModel):
        color: Color = None

    obj = Model(color=color).color
    assert obj.original() == color
    assert str(obj) == str(color).lower()
    assert obj.__repr__() == '<Color("{}")>'.format(obj._color_match)
    assert obj.as_named_color() == as_name
    assert obj.as_rgb(alpha=False) == 'rgb{}'.format(as_tuple)
    assert obj.as_rgb(alpha=True) == 'rgba{}'.format(as_tuple + (1.0,))
    assert obj.as_tuple(alpha=False) == as_tuple
    assert obj.as_tuple(alpha=True) == as_tuple + (1.0,)
    assert obj.as_hex(prefix='') == as_hex
    assert obj.as_hex(prefix='0x') == '0x{}'.format(as_hex)
    expanded_hex = as_hex if len(as_hex) == 6 else f'{as_hex[0]}{as_hex[0]}{as_hex[1]}{as_hex[1]}{as_hex[2]}{as_hex[2]}'
    assert obj.as_hex(prefix='0x', reduce=False) == '0x{}'.format(expanded_hex)

    r, g, b = obj.as_hls()
    assert almost_equal_floats(r, as_hls[0])
    assert almost_equal_floats(g, as_hls[1])
    assert almost_equal_floats(b, as_hls[2])


@pytest.mark.parametrize(
    'color',
    [
        # named colors
        'nosuchname',
        'chucknorris',
        # hex
        '#0000000',
        '#0000',
        '0x797979',
        '0x777',
        # rgb/rgba tuples
        (256, 256, 256),
        (0, 0, 1280),
        (0, 0, 1205, 0.1),
        (0, 0, 1128, 0.5),
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
    class Model(BaseModel):
        color: Color = None

    with pytest.raises(ValidationError):
        Model(color=color).as_named_color()


@pytest.mark.parametrize(
    'color, result',
    [
        ('rgb(0, 128, 0)', (0, 128, 0, 1.0)),
        ('rgb(255, 255, 0)', (255, 255, 0, 1.0)),
        ('rgb(255,255,0)', (255, 255, 0, 1.0)),
        ('RGB(255,   255,0)', (255, 255, 0, 1.0)),
        ('rgba(0, 128, 0, 0.5)', (0, 128, 0, 0.5)),
        ('rgba(255, 255, 0, 0.123)', (255, 255, 0, 0.123)),
        ('rgba(255,255,0,0.123)', (255, 255, 0, 0.123)),
        ('RGBA(255,   255,0,0.123)', (255, 255, 0, 0.123)),
    ],
)
def test_color_rgba_regex_success(color, result):
    assert Color._rgb_str_to_tuple(color) == result


@pytest.mark.parametrize(
    'color',
    ['rgb(1000000, 128, 0)', 'rgb(255, 255, 10000000)', 'rgba(0, 128, 0, 1110.5)', 'rgba(255, 255, 0, 1110.123)'],
)
def test_color_rgba_regex_fail(color):
    assert Color._rgb_str_to_tuple(color) is None


@pytest.mark.parametrize(
    'value, result',
    [
        ((255, 255, 255), (255, 255, 255)),
        ((0, 0, 0), (0, 0, 0)),
        ((0, 0, 0, 0, 0), None),
        ((0, 0, 0, 'hello'), None),
        (('hello', 'hello', 'hello'), None),
    ],
)
def test_color_tuple_to_rgb(value, result):
    assert Color._tuple_to_rgb(value) == result


@pytest.mark.parametrize(
    'color, result',
    [('FFF', 'FFFFFF'), ('FfF', 'FFffFF'), ('123', '112233'), ('F', 'F'), ('FFFF', 'FFFF'), ('222222', '222222')],
)
def test_color_expand_3_digit_hex(color, result):
    assert Color(color)._expand_3_digit_hex(color) == result


@pytest.mark.parametrize(
    'color, result',
    [('FFFFFF', 'FFF'), ('FFffFF', 'FfF'), ('112233', '123'), ('F', 'F'), ('FFFF', 'FFFF'), ('22', '22')],
)
def test_color_reduce_6_digit_hex(color, result):
    assert Color(color)._reduce_6_digit_hex(color) == result


@pytest.mark.parametrize(
    'rgb, hex_str',
    [((0, 0, 0), '000000'), ((255, 0, 0), 'ff0000'), ((128, 0, 128), '800080'), ((128, 255, 128), '80ff80')],
)
def test_color_rgb_to_hex(rgb, hex_str):
    assert Color(rgb)._rgb_to_hex(rgb) == hex_str


@pytest.mark.parametrize(
    'hex_str, rgb',
    [
        ('000000', (0, 0, 0)),
        ('0x000000', (0, 0, 0)),
        ('#000000', (0, 0, 0)),
        ('#000', (0, 0, 0)),
        ('0x000', (0, 0, 0)),
        ('ff0000', (255, 0, 0)),
        ('800080', (128, 0, 128)),
        ('80ff80', (128, 255, 128)),
    ],
)
def test_color_hex_to_rgb(hex_str, rgb):
    assert Color(hex_str)._hex_to_rgb(hex_str) == rgb


@pytest.mark.parametrize(
    'value, result',
    [
        (128, True),
        (0, True),
        (255, True),
        ('12', True),
        ('0', True),
        (256, False),
        (-1, False),
        ('hello', False),
        ('0x8', False),
    ],
)
def test_color_is_int_color(value, result):
    assert Color._is_int_color(value) == result
