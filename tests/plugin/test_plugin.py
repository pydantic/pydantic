import os

import pytest

pytestmark = pytest.mark.skipif(not os.getenv('TEST_PLUGIN'), reason='Test only with `TEST_PLUGIN` env var set.')


def test_plugin_usage():
    from pydantic import BaseModel

    class MyModel(BaseModel):
        x: int
        y: str

    m = MyModel(x='10', y='hello')
    assert m.x == 10
    assert m.y == 'hello'

    from example_plugin import log

    assert log == [
        "on_enter args=({'x': '10', 'y': 'hello'},) kwargs={'self_instance': MyModel()}",
        "on_success result=x=10 y='hello'",
    ]
