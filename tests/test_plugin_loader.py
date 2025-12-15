import importlib.metadata as importlib_metadata
import os
import warnings
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


class EntryPointWithError:
    def __init__(self, name, value, group):
        self.name = name
        self.value = value
        self.group = group

    def load(self):
        raise ImportError('Test simulated exception')


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
    mock_entry_4 = EntryPoint(name='test_plugin4', value='test_plugin:plugin4', group='non_pydantic')
    mock_dist = Dist([mock_entry_1, mock_entry_2, mock_entry_3, mock_entry_4])

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


def test_caching_of_loaded_plugins(reset_plugins):
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = 'test_plugin1,test_plugin2'
    res = loader.get_plugins()
    assert list(res) == ['test_plugin:plugin3']
    res = loader.get_plugins()
    assert list(res) == ['test_plugin:plugin3']


def test_load_same_plugin_multiple_times(reset_plugins):
    mock_entry_1 = EntryPoint(name='test_plugin1', value='test_plugin:plugin1', group='pydantic')
    mock_dist = Dist([mock_entry_1, mock_entry_1])

    os.environ.pop('PYDANTIC_DISABLE_PLUGINS', None)

    with patch.object(importlib_metadata, 'distributions', return_value=[mock_dist]):
        res = loader.get_plugins()
        assert list(res) == ['test_plugin:plugin1']


def test_loader_with_failing_plugin(reset_plugins):
    """
    Test that one failing plugin doesn't prevent others from loading.
    """
    mock_entry_1 = EntryPoint(name='test_plugin1', value='test_plugin:plugin1', group='pydantic')
    mock_entry_error = EntryPointWithError(name='test_plugin_error', value='test_plugin:error', group='pydantic')
    mock_entry_2 = EntryPoint(name='test_plugin2', value='test_plugin:plugin2', group='pydantic')
    mock_dist = Dist([mock_entry_1, mock_entry_error, mock_entry_2])

    os.environ.pop('PYDANTIC_DISABLE_PLUGINS', None)

    with patch.object(importlib_metadata, 'distributions', return_value=[mock_dist]):
        with warnings.catch_warnings(record=True) as wrn:
            warnings.simplefilter('always')
            res = loader.get_plugins()
            result = list(res)

            # Should load 2 successful plugins
            assert 'test_plugin:error' not in result
            assert result == ['test_plugin:plugin1', 'test_plugin:plugin2']

            # Should have a warning about the failed plugin
            assert 'ImportError' in str(wrn[0].message)
            assert 'test_plugin_error' in str(wrn[0].message)
            assert 'Test simulated exception' in str(wrn[0].message)
