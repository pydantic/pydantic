import dirty_equals
import pytest

from pydantic import BaseModel, ConfigDict, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        (('1', '2'), ('1', '2')),
        (['1', '2'], ('1', '2')),
        ({'1': 1, '2': 2}.keys(), ('1', '2')),
        ({'1': '1', '2': '2'}.values(), ('1', '2')),
        ({'1', '2'}, dirty_equals.IsOneOf(('1', '2'), ('2', '1'))),
        (frozenset(['1', '2']), dirty_equals.IsOneOf(('1', '2'), ('2', '1'))),
        ({'1': 1, '2': 2}, ValidationError),
    ],
)
def test_tuple_validation(value, expected):
    class Model(BaseModel):
        v: tuple[str, ...]

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_tuple_strict() -> None:
    class LaxModel(BaseModel):
        v: tuple[int, int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: tuple[int, int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=[1, 2]).v == (1, 2)
    assert LaxModel(v=['1', 2]).v == (1, 2)
    # List should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=[1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': ('v',), 'msg': 'Input should be a valid tuple', 'input': [1, 2]}
    ]
    # Strict in each list item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=('1', 2))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('v', 0), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
