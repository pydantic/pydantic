import os
import pytest


class SetEnv:
    def __init__(self):
        self.envars = set()

    def set(self, name, value):
        self.envars.add(name)
        os.environ[name] = value

    def clear(self):
        for n in self.envars:
            os.environ.pop(n)


@pytest.yield_fixture
def env():
    setenv = SetEnv()

    yield setenv

    setenv.clear()
