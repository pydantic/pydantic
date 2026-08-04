import pytest

from pydantic import TypeAdapter, ValidationError


def test_dict():
    ta = TypeAdapter(dict)

    assert ta.validate_python({1: 10, 2: 20}) == {1: 10, 2: 20}
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([(1, 2), (3, 4)])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dict_type',
            'loc': (),
            'msg': 'Input should be a valid dictionary',
            'input': [(1, 2), (3, 4)],
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]
