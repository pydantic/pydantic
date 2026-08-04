from typing import Literal, Optional

import pytest

from pydantic import BaseModel, Json, TypeAdapter, ValidationError


def test_optional():
    ta = TypeAdapter(Optional[int])  # noqa: UP045

    assert ta.validate_python(None) is None
    assert ta.validate_python(1) == 1


@pytest.mark.parametrize('value_type', (None, type(None)))
def test_none(value_type):
    class Model(BaseModel):
        my_none: value_type
        my_none_list: list[value_type]
        my_none_dict: dict[str, value_type]
        my_json_none: Json[value_type]

    Model(
        my_none=None,
        my_none_list=[None] * 3,
        my_none_dict={'a': None, 'b': None},
        my_json_none='null',
    )

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'my_none': {'type': 'null', 'title': 'My None'},
            'my_none_list': {'type': 'array', 'items': {'type': 'null'}, 'title': 'My None List'},
            'my_none_dict': {'type': 'object', 'additionalProperties': {'type': 'null'}, 'title': 'My None Dict'},
            'my_json_none': {
                'contentMediaType': 'application/json',
                'contentSchema': {'type': 'null'},
                'title': 'My Json None',
                'type': 'string',
            },
        },
        'required': ['my_none', 'my_none_list', 'my_none_dict', 'my_json_none'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(
            my_none='qwe',
            my_none_list=[1, None, 'qwe'],
            my_none_dict={'a': 1, 'b': None},
            my_json_none='"a"',
        )
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': ('my_none',), 'msg': 'Input should be None', 'input': 'qwe'},
        {'type': 'none_required', 'loc': ('my_none_list', 0), 'msg': 'Input should be None', 'input': 1},
        {
            'type': 'none_required',
            'loc': ('my_none_list', 2),
            'msg': 'Input should be None',
            'input': 'qwe',
        },
        {
            'type': 'none_required',
            'loc': ('my_none_dict', 'a'),
            'msg': 'Input should be None',
            'input': 1,
        },
        {'type': 'none_required', 'loc': ('my_json_none',), 'msg': 'Input should be None', 'input': 'a'},
    ]


def test_none_literal():
    class Model(BaseModel):
        my_none: Literal[None]
        my_none_list: list[Literal[None]]
        my_none_dict: dict[str, Literal[None]]
        my_json_none: Json[Literal[None]]

    Model(
        my_none=None,
        my_none_list=[None] * 3,
        my_none_dict={'a': None, 'b': None},
        my_json_none='null',
    )

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'my_none': {'const': None, 'title': 'My None', 'type': 'null'},
            'my_none_list': {
                'items': {'const': None, 'type': 'null'},
                'title': 'My None List',
                'type': 'array',
            },
            'my_none_dict': {
                'additionalProperties': {'const': None, 'type': 'null'},
                'title': 'My None Dict',
                'type': 'object',
            },
            'my_json_none': {
                'contentMediaType': 'application/json',
                'contentSchema': {'const': None, 'type': 'null'},
                'title': 'My Json None',
                'type': 'string',
            },
        },
        'required': ['my_none', 'my_none_list', 'my_none_dict', 'my_json_none'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(
            my_none='qwe',
            my_none_list=[1, None, 'qwe'],
            my_none_dict={'a': 1, 'b': None},
            my_json_none='"a"',
        )
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('my_none',),
            'msg': 'Input should be None',
            'input': 'qwe',
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_none_list', 0),
            'msg': 'Input should be None',
            'input': 1,
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_none_list', 2),
            'msg': 'Input should be None',
            'input': 'qwe',
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_none_dict', 'a'),
            'msg': 'Input should be None',
            'input': 1,
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_json_none',),
            'msg': 'Input should be None',
            'input': 'a',
            'ctx': {'expected': 'None'},
        },
    ]
