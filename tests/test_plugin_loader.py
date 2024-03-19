import importlib.metadata as importlib_metadata
import os
from unittest.mock import patch

import pytest

import pydantic.plugin._loader as loader


class EntryPoint:
    def __init__(self, name, value, group):
        self.name = name
        self.value = value
        self.group = group

    def load(self):
        return self.value


class Dist:
    entry_points = []

    def __init__(self, entry_points):
        self.entry_points = entry_points


@pytest.fixture
def reset_plugins():
    global loader
    initial_plugins = loader._plugins
    loader._plugins = None
    yield
    # teardown
    loader._plugins = initial_plugins


@pytest.fixture(autouse=True)
def mock():
    mock_entry_1 = EntryPoint(name='test_plugin1', value='test_plugin:plugin1', group='pydantic')
    mock_entry_2 = EntryPoint(name='test_plugin2', value='test_plugin:plugin2', group='pydantic')
    mock_entry_3 = EntryPoint(name='test_plugin3', value='test_plugin:plugin3', group='pydantic')
    mock_dist = Dist([mock_entry_1, mock_entry_2, mock_entry_3])

    with patch.object(importlib_metadata, 'distributions', return_value=[mock_dist]):
        yield


def test_loader(reset_plugins):
    res = loader.get_plugins()
    assert list(res) == ['test_plugin:plugin1', 'test_plugin:plugin2', 'test_plugin:plugin3']


def test_disable_all(reset_plugins):
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = '__all__'
    res = loader.get_plugins()
    assert res == ()


def test_disable_all_1(reset_plugins):
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = '1'
    res = loader.get_plugins()
    assert res == ()


def test_disable_true(reset_plugins):
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = 'true'
    res = loader.get_plugins()
    assert res == ()


def test_disable_one(reset_plugins):
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = 'test_plugin1'
    res = loader.get_plugins()
    assert len(list(res)) == 2
    assert 'test_plugin:plugin1' not in list(res)


def test_disable_multiple(reset_plugins):
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = 'test_plugin1,test_plugin2'
    res = loader.get_plugins()
    assert len(list(res)) == 1
    assert 'test_plugin:plugin1' not in list(res)
    assert 'test_plugin:plugin2' not in list(res)
