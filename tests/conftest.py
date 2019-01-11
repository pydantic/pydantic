import os
import secrets
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
        name = f'test_code_{secrets.token_hex(5)}'
        path = tmp_path / f'{name}.py'
        path.write_text(code)
        return SourceFileLoader(name, str(path)).load_module()

    return run
