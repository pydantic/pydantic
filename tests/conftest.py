import os
from importlib.machinery import SourceFileLoader

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


@pytest.fixture
def create_module(tmp_path):
    def run(code):
        path = tmp_path / 'test_code.py'
        path.write_text(code)
        return SourceFileLoader('test_code', str(path)).load_module()

    return run
