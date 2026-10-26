import math
import platform
from typing import Annotated

import pytest

from pydantic import Field, TypeAdapter, ValidationError


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy',
    reason='PyPy has a bug in complex string parsing. A fix is implemented but not yet released.',
)
def test_complex_validation():
    ta = TypeAdapter(complex)

    assert ta.validate_python(complex(1, 2)) == complex(1, 2)
    assert ta.dump_json(complex(1, 2)) == b'"1+2j"'

    # Complex numbers presented as strings are also acceptable
    assert ta.validate_python('1+2j') == complex(1, 2)

    # The part that is 0 can be omitted
    assert ta.validate_python('1') == complex(1, 0)
    assert ta.validate_python('1j') == complex(0, 1)
    assert ta.validate_python('0') == complex(0, 0)

    assert ta.validate_python('infj') == complex(0, float('inf'))

    v = ta.validate_python('-nanj')
    assert v.real == 0
    assert math.isnan(v.imag)
    assert ta.dump_json(v) == b'"NaNj"'

    # strings with brackets and space characters are allowed as long as
    # they follow the rule
    assert ta.validate_python('\t( -1.23+4.5J )\n') == complex(-1.23, 4.5)

    # int and float are also accepted (with imaginary part == 0)
    assert ta.validate_python(2) == complex(2, 0)
    assert ta.validate_python(1.5) == complex(1.5, 0)

    # Empty strings are not allowed
    with pytest.raises(ValidationError):
        ta.validate_python('')
    with pytest.raises(ValidationError):
        ta.validate_python('foo')
    # Bracket missing
    with pytest.raises(ValidationError):
        ta.validate_python('\t( -1.23+4.5J \n')
    # Space between numbers
    with pytest.raises(ValidationError):
        ta.validate_python('\t( -1.23 +4.5J \n')


def test_strict_complex():
    # Only complex objects are accepted
    ta = TypeAdapter(Annotated[complex, Field(strict=True)])

    assert ta.validate_python(complex(1, 2)) == complex(1, 2)

    with pytest.raises(ValidationError):
        ta.validate_python('1+2j')
    with pytest.raises(ValidationError):
        ta.validate_python(1.0)
    with pytest.raises(ValidationError):
        ta.validate_python(5)
