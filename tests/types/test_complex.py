import math
import platform
from typing import Annotated

import pytest

from pydantic import BaseModel, Field, ValidationError


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy',
    reason='PyPy has a bug in complex string parsing. A fix is implemented but not yet released.',
)
def test_complex_field():
    class Model(BaseModel):
        number: complex

    m = Model(number=complex(1, 2))
    assert repr(m) == 'Model(number=(1+2j))'
    assert m.model_dump() == {'number': complex(1, 2)}
    assert m.model_dump_json() == '{"number":"1+2j"}'

    # Complex numbers presented as strings are also acceptable
    m = Model(number='1+2j')
    assert repr(m) == 'Model(number=(1+2j))'
    assert m.model_dump() == {'number': complex(1, 2)}
    assert m.model_dump_json() == '{"number":"1+2j"}'

    # The part that is 0 can be omitted
    m = Model(number='1')
    assert repr(m) == 'Model(number=(1+0j))'
    assert m.model_dump() == {'number': complex(1, 0)}
    assert m.model_dump_json() == '{"number":"1+0j"}'

    m = Model(number='1j')
    assert repr(m) == 'Model(number=1j)'
    assert m.model_dump() == {'number': complex(0, 1)}
    assert m.model_dump_json() == '{"number":"1j"}'

    m = Model(number='0')
    assert repr(m) == 'Model(number=0j)'
    assert m.model_dump() == {'number': complex(0, 0)}
    assert m.model_dump_json() == '{"number":"0j"}'

    m = Model(number='infj')
    assert repr(m) == 'Model(number=infj)'
    assert m.model_dump() == {'number': complex(0, float('inf'))}
    assert m.model_dump_json() == '{"number":"infj"}'

    m = Model(number='-nanj')
    assert repr(m) == 'Model(number=nanj)'
    d = m.model_dump()
    assert d['number'].real == 0
    assert math.isnan(d['number'].imag)
    assert m.model_dump_json() == '{"number":"NaNj"}'

    # strings with brackets and space characters are allowed as long as
    # they follow the rule
    m = Model(number='\t( -1.23+4.5J )\n')
    assert repr(m) == 'Model(number=(-1.23+4.5j))'
    assert m.model_dump() == {'number': complex(-1.23, 4.5)}
    assert m.model_dump_json() == '{"number":"-1.23+4.5j"}'

    # int and float are also accepted (with imaginary part == 0)
    m = Model(number=2)
    assert repr(m) == 'Model(number=(2+0j))'
    assert m.model_dump() == {'number': complex(2, 0)}
    assert m.model_dump_json() == '{"number":"2+0j"}'

    m = Model(number=1.5)
    assert repr(m) == 'Model(number=(1.5+0j))'
    assert m.model_dump() == {'number': complex(1.5, 0)}
    assert m.model_dump_json() == '{"number":"1.5+0j"}'

    # Empty strings are not allowed
    with pytest.raises(ValidationError):
        Model(number='')
    with pytest.raises(ValidationError):
        Model(number='foo')
    # Bracket missing
    with pytest.raises(ValidationError):
        Model(number='\t( -1.23+4.5J \n')
    # Space between numbers
    with pytest.raises(ValidationError):
        Model(number='\t( -1.23 +4.5J \n')


def test_strict_complex_field():
    class Model(BaseModel):
        # Only complex objects are accepted
        number: Annotated[complex, Field(strict=True)]

    m = Model(number=complex(1, 2))
    assert repr(m) == 'Model(number=(1+2j))'
    assert m.model_dump() == {'number': complex(1, 2)}
    assert m.model_dump_json() == '{"number":"1+2j"}'

    with pytest.raises(ValidationError):
        m = Model(number='1+2j')
    with pytest.raises(ValidationError):
        m = Model(number=1.0)
    with pytest.raises(ValidationError):
        m = Model(number=5)
