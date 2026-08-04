from collections import deque
from collections.abc import Sequence
from typing import Any

import pytest

from pydantic import BaseModel, PydanticSchemaGenerationError, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'cls, value,result',
    (
        (int, [1, 2, 3], [1, 2, 3]),
        (int, (1, 2, 3), (1, 2, 3)),
        (int, range(5), [0, 1, 2, 3, 4]),
        (int, deque((1, 2, 3)), deque((1, 2, 3))),
        (set[int], [{1, 2}, {3, 4}, {5, 6}], [{1, 2}, {3, 4}, {5, 6}]),
        (tuple[int, str], ((1, 'a'), (2, 'b'), (3, 'c')), ((1, 'a'), (2, 'b'), (3, 'c'))),
    ),
)
def test_sequence_success(cls, value, result):
    class Model(BaseModel):
        v: Sequence[cls]

    assert Model(v=value).v == result


def test_sequence_generator_fails():
    class Model(BaseModel):
        v: Sequence[int]

    gen = (i for i in [1, 2, 3])
    with pytest.raises(ValidationError) as exc_info:
        Model(v=gen)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('v',),
            'msg': 'Input should be an instance of Sequence',
            'input': gen,
            'ctx': {'class': 'Sequence'},
        }
    ]


@pytest.mark.parametrize(
    'cls,value,errors',
    (
        (
            int,
            [1, 'a', 3],
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 1),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'a',
                },
            ],
        ),
        (
            int,
            (1, 2, 'a'),
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'a',
                },
            ],
        ),
        (
            float,
            ('a', 2.2, 3.3),
            [
                {
                    'type': 'float_parsing',
                    'loc': ('v', 0),
                    'msg': 'Input should be a valid number, unable to parse string as a number',
                    'input': 'a',
                },
            ],
        ),
        (
            float,
            (1.1, 2.2, 'a'),
            [
                {
                    'type': 'float_parsing',
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid number, unable to parse string as a number',
                    'input': 'a',
                },
            ],
        ),
        (
            float,
            {1.0, 2.0, 3.0},
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of Sequence',
                    'input': {
                        1.0,
                        2.0,
                        3.0,
                    },
                    'ctx': {
                        'class': 'Sequence',
                    },
                },
            ],
        ),
        (
            set[int],
            [{1, 2}, {2, 3}, {'d'}],
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 2, 0),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'd',
                }
            ],
        ),
        (
            tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 1, 0),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'a',
                }
            ],
        ),
        (
            list[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            [
                {
                    'type': 'list_type',
                    'loc': ('v', 0),
                    'msg': 'Input should be a valid list',
                    'input': {'a': 1, 'b': 2},
                }
            ],
        ),
    ),
    ids=repr,
)
def test_sequence_fails(cls, value, errors):
    class Model(BaseModel):
        v: Sequence[cls]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors(include_url=False) == errors


def test_sequence_strict():
    assert TypeAdapter(Sequence[int]).validate_python((), strict=True) == ()


def test_sequence_subclass_without_core_schema() -> None:
    class MyList(list[int]):
        # The point of this is that subclasses can do arbitrary things
        # This is the reason why we don't try to handle them automatically
        # TBD if we introspect `__init__` / `__new__`
        # (which is the main thing that would mess us up if modified in a subclass)
        # and automatically handle cases where the subclass doesn't override it.
        # There's still edge cases (again, arbitrary behavior...)
        # and it's harder to explain, but could lead to a better user experience in some cases
        # It will depend on how the complaints (which have and will happen in both directions)
        # balance out
        def __init__(self, *args: Any, required: int, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)

    with pytest.raises(
        PydanticSchemaGenerationError, match='implement `__get_pydantic_core_schema__` on your type to fully support it'
    ):

        class _(BaseModel):
            x: MyList


def test_can_serialize_deque_passed_to_sequence() -> None:
    ta = TypeAdapter(Sequence[int])
    my_dec = ta.validate_python(deque([1, 2, 3]))
    assert my_dec == deque([1, 2, 3])

    assert ta.dump_python(my_dec) == my_dec
    assert ta.dump_json(my_dec) == b'[1,2,3]'


@pytest.mark.parametrize('sequence_type', [list, tuple, deque])
def test_sequence_with_nested_type(sequence_type: type) -> None:
    class Model(BaseModel):
        a: int

    class OuterModel(BaseModel):
        inner: Sequence[Model]

    models = sequence_type([Model(a=1), Model(a=2)])
    assert OuterModel(inner=models).model_dump() == {'inner': sequence_type([{'a': 1}, {'a': 2}])}
