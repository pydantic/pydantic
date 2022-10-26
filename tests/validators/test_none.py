import pytest

from pydantic_core import ValidationError

from ..conftest import PyAndJson


def test_none(py_and_json: PyAndJson):
    v = py_and_json({'type': 'none'})
    assert v.validate_test(None) is None
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(1)
    assert exc_info.value.errors() == [
        {'type': 'none_required', 'loc': (), 'msg': 'Input should be None/null', 'input': 1}
    ]
