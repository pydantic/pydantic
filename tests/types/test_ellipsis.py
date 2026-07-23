from types import EllipsisType

import pytest
from pydantic_core import PydanticSerializationError, PydanticSerializationUnexpectedValue

from pydantic import TypeAdapter


def test_ellipsis_literal() -> None:
    ta = TypeAdapter(EllipsisType)

    assert ta.validate_python(...) is ...
    assert ta.dump_python(...) is ...

    with pytest.raises(PydanticSerializationUnexpectedValue):
        ta.dump_python(1)

    with pytest.raises(
        PydanticSerializationError, match="Error serializing to JSON: 'Ellipsis' can't be serialized to JSON"
    ):
        ta.dump_json(...)
