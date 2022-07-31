import pytest

from pydantic_core import ValidationError

from ..conftest import PyAndJson


def test_none(py_and_json: PyAndJson):
    v = py_and_json('none')
    assert v.validate_test(None) is None
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(1)
    assert exc_info.value.errors() == [
        {'kind': 'none_required', 'loc': [], 'message': 'Input should be None/null', 'input_value': 1}
    ]
