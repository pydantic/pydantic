import pytest


def test_plugin_usage():
    from pydantic import BaseModel

    with pytest.warns(UserWarning, match='AttributeError while loading the `my_plugin` Pydantic plugin.*'):

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
