from __future__ import annotations

import contextlib
import sys
from typing import Any, Generator

import pytest
from pydantic_core import ValidationError

from pydantic import BaseModel
from pydantic.plugin import OnValidateJsonProtocol, OnValidatePythonProtocol, Plugin
from pydantic.plugin._loader import _plugins


@pytest.fixture
def unimport_pydantic():
    # Force an actual import of anything that is part of pydantic
    unimported_modules = {}
    if 'pydantic' in sys.modules:
        unimported_modules['pydantic'] = sys.modules.pop('pydantic')
    pydantic_modules = set()
    for module_name in sys.modules:
        if module_name.startswith('pydantic.'):
            pydantic_modules.add(module_name)
    for module_name in pydantic_modules:
        unimported_modules[module_name] = sys.modules.pop(module_name)

    yield

    for module_name, module in unimported_modules.items():
        sys.modules[module_name] = module


@contextlib.contextmanager
def install_plugin(plugin: Plugin) -> Generator[None, None, None]:
    _plugins[plugin.__class__.__qualname__] = plugin
    yield
    _plugins.clear()


def test_on_validate_json_on_success() -> None:
    class CustomOnValidateJson(OnValidateJsonProtocol):
        def on_enter(
            self,
            input: str | bytes | bytearray,
            *,
            strict: bool | None = None,
            context: dict[str, Any] | None = None,
            self_instance: Any | None = None,
        ) -> None:
            assert input == '{"a": 1}'
            assert strict is None
            assert context is None
            assert self_instance is None
            assert self.config == {'title': 'Model'}
            assert self.plugin_settings == {'observe': 'all'}

        def on_success(self, result: Any) -> None:
            assert isinstance(result, Model)

    plugin = Plugin(on_validate_json=CustomOnValidateJson)
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        Model.model_validate({'a': 1}) == {'a': 1}
        Model.model_validate_json('{"a": 1}') == {'a': 1}


def test_on_validate_json_on_error() -> None:
    class CustomOnValidateJson(OnValidateJsonProtocol):
        def enter(
            self,
            input: str | bytes | bytearray,
            *,
            strict: bool | None = None,
            context: dict[str, Any] | None = None,
            self_instance: Any | None = None,
        ) -> None:
            assert input == '{"a": "potato"}'
            assert strict is None
            assert context is None
            assert self_instance is None
            assert self.config == {'title': 'Model'}
            assert self.plugin_settings == {'observe': 'all'}

        def on_error(self, error: ValidationError) -> None:
            assert error.title == 'Model'
            assert error.errors() == [
                {
                    'input': 'potato',
                    'loc': ('a',),
                    'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
                    'type': 'int_parsing',
                    'url': 'https://errors.pydantic.dev/2.3/v/int_parsing',
                },
            ]

    plugin = Plugin(on_validate_json=CustomOnValidateJson)
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        Model.model_validate({'a': 1}) == {'a': 1}
        with contextlib.suppress(ValidationError):
            Model.model_validate_json('{"a": "potato"}')


def test_on_validate_python_on_success() -> None:
    class CustomOnValidatePython(OnValidatePythonProtocol):
        def enter(
            self,
            input: Any,
            *,
            strict: bool | None = None,
            from_attributes: bool | None = None,
            context: dict[str, Any] | None = None,
            self_instance: Any | None = None,
        ) -> None:
            assert input == {'a': 1}
            assert strict is None
            assert context is None
            assert self_instance is None
            assert self.config == {'title': 'Model'}
            assert self.plugin_settings == {'observe': 'all'}

        def on_success(self, result: Any) -> None:
            assert isinstance(result, Model)

    plugin = Plugin(on_validate_python=CustomOnValidatePython)
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        Model.model_validate({'a': 1}) == {'a': 1}
        Model.model_validate_json('{"a": 1}') == {'a': 1}


def test_on_validate_python_on_error() -> None:
    class CustomOnValidatePython(OnValidatePythonProtocol):
        def enter(
            self,
            input: Any,
            *,
            strict: bool | None = None,
            from_attributes: bool | None = None,
            context: dict[str, Any] | None = None,
            self_instance: Any | None = None,
        ) -> None:
            assert input == {'a': 'potato'}
            assert strict is None
            assert context is None
            assert self_instance is None
            assert self.config == {'title': 'Model'}
            assert self.plugin_settings == {'observe': 'all'}

        def on_error(self, error: ValidationError) -> None:
            assert error.title == 'Model'
            assert error.errors() == [
                {
                    'input': 'potato',
                    'loc': ('a',),
                    'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
                    'type': 'int_parsing',
                    'url': 'https://errors.pydantic.dev/2.3/v/int_parsing',
                },
            ]

    plugin = Plugin(on_validate_python=CustomOnValidatePython)
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        with contextlib.suppress(ValidationError):
            Model.model_validate({'a': 'potato'})
        Model.model_validate_json('{"a": 1}') == {'a': 1}


def test_using_pydantic_inside_plugin():
    class TestPlugin(OnValidatePythonProtocol):
        def on_enter(
            self,
            input: Any,
            *,
            strict: bool | None = None,
            from_attributes: bool | None = None,
            context: dict[str, Any] | None = None,
            self_instance: Any | None = None,
        ) -> None:
            from pydantic import TypeAdapter

            assert TypeAdapter(int).validate_python(42)

    plugin = Plugin(on_validate_python=TestPlugin)
    with install_plugin(plugin):

        class Model(BaseModel):
            a: int

        assert Model(a=42).model_dump() == {'a': 42}


def test_fresh_import_using_pydantic_inside_plugin(monkeypatch: pytest.MonkeyPatch, unimport_pydantic):
    def fake_distributions():
        class FakeOnValidatePython(OnValidatePythonProtocol):
            def on_enter(
                self,
                input: Any,
                *,
                strict: bool | None = None,
                from_attributes: bool | None = None,
                context: dict[str, Any] | None = None,
                self_instance: Any | None = None,
            ) -> None:
                pass

            def on_success(self, result: Any) -> None:
                pass

            def on_error(self, error: ValidationError) -> None:
                pass

        class FakeEntryPoint:
            group = 'pydantic'
            value = 'pydantic.tests.Plugin'

            def load(self):
                # Emulate performing the same import that caused loading plugin while importing a plugin module
                from pydantic import BaseModel  # noqa: F401

                return Plugin(on_validate_python=FakeOnValidatePython)

        class FakeDistribution:
            entry_points = [FakeEntryPoint()]

        return [FakeDistribution()]

    if sys.version_info >= (3, 8):
        monkeypatch.setattr('importlib.metadata.distributions', fake_distributions)
    else:
        monkeypatch.setattr('importlib_metadata.distributions', fake_distributions)

    from pydantic import BaseModel

    class Model(BaseModel):
        a: int

    assert Model(a=42).model_dump() == {'a': 42}


def test_fresh_import_using_example_plugin(monkeypatch: pytest.MonkeyPatch, unimport_pydantic):
    def fake_distributions():
        class ExampleEntryPoint:
            group = 'pydantic'
            value = 'pydantic.tests.example_plugin.plugin:plugin'

            def load(self):
                from .example_plugin.plugin import plugin

                return plugin

        class ExampleDistribution:
            entry_points = [ExampleEntryPoint()]

        return [ExampleDistribution()]

    if sys.version_info >= (3, 8):
        monkeypatch.setattr('importlib.metadata.distributions', fake_distributions)
    else:
        monkeypatch.setattr('importlib_metadata.distributions', fake_distributions)

    assert [name for name in sys.modules if name == 'pydantic' or name.startswith('pydantic.')] == []

    with pytest.warns(UserWarning, match='Error while running a Pydantic plugin'):
        from . import example_plugin

    assert example_plugin.m.model_dump() == {'value': 'abc'}
