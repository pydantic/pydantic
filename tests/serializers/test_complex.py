import math

import pytest

from pydantic_core import SchemaSerializer, core_schema


@pytest.mark.parametrize(
    'value,expected',
    [
        (complex(-1.23e-4, 567.89), '-0.000123+567.89j'),
        (complex(0, -1.23), '-1.23j'),
        (complex(1.5, 0), '1.5+0j'),
        (complex(1, 2), '1+2j'),
        (complex(0, 1), '1j'),
        (complex(0, 1e-500), '0j'),
        (complex(-float('inf'), 2), '-inf+2j'),
        (complex(float('inf'), 2), 'inf+2j'),
        (complex(float('nan'), 2), 'NaN+2j'),
    ],
)
def test_complex_json(value, expected):
    v = SchemaSerializer(core_schema.complex_schema())
    c = v.to_python(value)
    c_json = v.to_python(value, mode='json')
    json_str = v.to_json(value).decode()

    assert c_json == expected
    assert json_str == f'"{expected}"'

    if math.isnan(value.imag):
        assert math.isnan(c.imag)
    else:
        assert c.imag == value.imag

    if math.isnan(value.real):
        assert math.isnan(c.real)
    else:
        assert c.imag == value.imag
