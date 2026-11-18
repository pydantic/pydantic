from fractions import Fraction
from typing import Annotated

import pytest
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, ByteSize, Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'size,decimal,expected',
    [
        (1023, False, '1023B'),
        (1048575, False, '1.0MiB'),
        (-1048575, False, '-1.0MiB'),
        (1024**5 * 1024 - 1, False, '1.0EiB'),
        (999, True, '999B'),
        (999_999, True, '1.0MB'),
        (999_949, True, '999.9KB'),
    ],
)
def test_bytesize_human_readable_unit_boundary(size: int, decimal: bool, expected: str) -> None:
    """https://github.com/pydantic/pydantic/issues/14056"""

    assert ByteSize(size).human_readable(decimal=decimal) == expected


@pytest.mark.parametrize(
    'input_value,output,human_bin,human_dec,human_sep',
    (
        pytest.param(1, 1, '1B', '1B', '1 B', id='1_int-1_int-1B-1B-1 B'),
        pytest.param('1', 1, '1B', '1B', '1 B', id='1_str-1_int-1B-1B-1 B'),
        ('1.0', 1, '1B', '1B', '1 B'),
        ('1b', 1, '1B', '1B', '1 B'),
        ('1.5 KB', int(1.5e3), '1.5KiB', '1.5KB', '1.5 KiB'),
        ('1.5 K', int(1.5e3), '1.5KiB', '1.5KB', '1.5 KiB'),
        ('1.5 MB', int(1.5e6), '1.4MiB', '1.5MB', '1.4 MiB'),
        ('1.5 M', int(1.5e6), '1.4MiB', '1.5MB', '1.4 MiB'),
        ('5.1kib', 5222, '5.1KiB', '5.2KB', '5.1 KiB'),
        ('6.2EiB', 7148113328562451251, '6.2EiB', '7.1EB', '6.2 EiB'),
        ('8bit', 1, '1B', '1B', '1 B'),
        ('1kbit', 125, '125B', '125B', '125 B'),
    ),
)
def test_bytesize_conversions(input_value, output, human_bin, human_dec, human_sep):
    class Model(BaseModel):
        size: ByteSize

    m = Model(size=input_value)

    assert m.size == output

    assert m.size.human_readable() == human_bin
    assert m.size.human_readable(decimal=True) == human_dec
    assert m.size.human_readable(separator=' ') == human_sep


def test_bytesize_to():
    class Model(BaseModel):
        size: ByteSize

    m = Model(size='1GiB')

    assert m.size.to('MiB') == pytest.approx(1024)
    assert m.size.to('MB') == pytest.approx(1073.741824)
    assert m.size.to('TiB') == pytest.approx(0.0009765625)
    assert m.size.to('bit') == pytest.approx(8589934592)
    assert m.size.to('kbit') == pytest.approx(8589934.592)


def test_bytesize_raises():
    class Model(BaseModel):
        size: ByteSize

    with pytest.raises(ValidationError, match='parse value') as exc_info:
        Model(size='d1MB')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'd1MB',
            'loc': ('size',),
            'msg': 'could not parse value and unit from byte string',
            'type': 'byte_size',
        }
    ]

    with pytest.raises(ValidationError, match='parse value') as exc_info:
        Model(size='1' * 5000 + 'KB')

    with pytest.raises(ValidationError, match='byte unit') as exc_info:
        Model(size='1LiB')
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'unit': 'LiB'},
            'input': '1LiB',
            'loc': ('size',),
            'msg': 'could not interpret byte unit: LiB',
            'type': 'byte_size_unit',
        }
    ]

    # 1Gi is not a valid unit unlike 1G
    with pytest.raises(ValidationError, match='byte unit'):
        Model(size='1Gi')

    m = Model(size='1MB')
    with pytest.raises(PydanticCustomError, match='byte unit'):
        m.size.to('bad_unit')

    with pytest.raises(PydanticCustomError, match='byte unit'):
        m.size.to('1ZiB')


@pytest.mark.parametrize(
    'input_value,output',
    [
        ('1.005 KB', 1005),
        ('1.003 KB', 1003),
        ('1.0049 KB', 1004),
        ('9007199254740993 B', 9007199254740993),
        ('9007199254740993 KB', 9007199254740993000),
        ('1.5 kbit', 187),
        ('1' * 310 + 'KB', int('1' * 310) * 1000),
    ],
)
def test_bytesize_exact_conversion(input_value: str, output: int) -> None:
    """Regression test for https://github.com/pydantic/pydantic/issues/14297."""
    ta = TypeAdapter(ByteSize)

    assert ta.validate_python(input_value) == output
    assert ta.validate_json(f'"{input_value}"') == output


def test_bytesize_exact_conversion_constraints() -> None:
    """Regression test for https://github.com/pydantic/pydantic/issues/14297."""
    with pytest.raises(ValidationError):
        TypeAdapter(Annotated[ByteSize, Field(le=1004)]).validate_python('1.005 KB')
    assert TypeAdapter(Annotated[ByteSize, Field(ge=1005)]).validate_python('1.005 KB') == 1005


def test_bytesize_byte_sizes_exact() -> None:
    """The unit multipliers must be exactly representable, for `ByteSize` validation to be exact."""
    expected = {'b': Fraction(1), 'bit': Fraction(1, 8)}
    for i, prefix in enumerate('kmgtpe', start=1):
        expected[f'{prefix}b'] = expected[prefix] = Fraction(10 ** (3 * i))
        expected[f'{prefix}bit'] = Fraction(10 ** (3 * i), 8)
        expected[f'{prefix}ib'] = Fraction(2 ** (10 * i))
        expected[f'{prefix}ibit'] = Fraction(2 ** (10 * i), 8)

    assert {unit: Fraction(mult) for unit, mult in ByteSize.byte_sizes.items()} == expected
