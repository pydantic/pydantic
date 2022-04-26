import pytest


@pytest.mark.parametrize('input_value,expected', [([1, 2, 3], [1, 2, 3]), ([1, 2, '3'], [1, 2, 3])])
def test_list(py_or_json, input_value, expected):
    v = py_or_json({'type': 'list', 'items': {'type': 'int'}})
    assert v.validate_test(input_value) == expected
