import pytest

from pydantic import PydanticTypeError


def test_pydantic_error():
    class TestError(PydanticTypeError):
        code = 'test_code'
        msg_template = 'test message template "{test_ctx}"'

        def __init__(self, *, test_ctx: int) -> None:
            super().__init__(test_ctx=test_ctx)

    with pytest.raises(TestError) as exc_info:
        raise TestError(test_ctx='test_value')
    assert str(exc_info.value) == 'test message template "test_value"'
