"""
New tests for v2 of serialization logic.
"""
from typing import Any, Optional

import pytest
from pydantic_core import PydanticSerializationError, core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, serializer


def test_serialize_decorator_always():
    class MyModel(BaseModel):
        x: Optional[int]

        @serializer('x', json_return_type='str')
        def customise_x_serialisation(cls, v, _info):
            return f'{v:,}'

    assert MyModel(x=1234).model_dump() == {'x': '1,234'}
    assert MyModel(x=1234).model_dump(mode='json') == {'x': '1,234'}
    assert MyModel(x=1234).model_dump_json() == b'{"x":"1,234"}'
    m = MyModel(x=None)
    # can't use v:, on None, hence error
    error_msg = (
        'Error calling function `customise_x_serialisation`: '
        'TypeError: unsupported format string passed to NoneType.__format__'
    )
    with pytest.raises(PydanticSerializationError, match=error_msg):
        m.model_dump()
    with pytest.raises(PydanticSerializationError, match=error_msg):
        m.model_dump_json()


def test_serialize_decorator_json():
    class MyModel(BaseModel):
        x: int

        @serializer('x', json_return_type='str', when_used='json')
        def customise_x_serialisation(cls, v, _info):
            return f'{v:,}'

    assert MyModel(x=1234).model_dump() == {'x': 1234}
    assert MyModel(x=1234).model_dump(mode='json') == {'x': '1,234'}
    assert MyModel(x=1234).model_dump_json() == b'{"x":"1,234"}'


def test_serialize_decorator_unless_none():
    class MyModel(BaseModel):
        x: Optional[int]

        @serializer('x', when_used='unless-none')
        def customise_x_serialisation(cls, v, _info):
            return f'{v:,}'

    assert MyModel(x=1234).model_dump() == {'x': '1,234'}
    assert MyModel(x=None).model_dump() == {'x': None}
    assert MyModel(x=1234).model_dump(mode='json') == {'x': '1,234'}
    assert MyModel(x=None).model_dump(mode='json') == {'x': None}
    assert MyModel(x=1234).model_dump_json() == b'{"x":"1,234"}'
    assert MyModel(x=None).model_dump_json() == b'{"x":null}'


def test_annotated_customisation():
    def parse_int(s: str, _: Any) -> int:
        return int(s.replace(',', ''))

    class CommaFriendlyIntLogic:
        @classmethod
        def __get_pydantic_core_schema__(cls, _schema):
            # here we ignore the schema argument (which is just `{'type': 'int'}`) and return our own
            return core_schema.general_before_validation_function(
                parse_int,
                core_schema.int_schema(),
                serialization=core_schema.format_ser_schema(',', when_used='unless-none'),
            )

    CommaFriendlyInt = Annotated[int, CommaFriendlyIntLogic]

    class MyModel(BaseModel):
        x: CommaFriendlyInt

    m = MyModel(x='1,000')
    assert m.x == 1000
    assert m.model_dump(mode='json') == {'x': '1,000'}
    assert m.model_dump_json() == b'{"x":"1,000"}'
