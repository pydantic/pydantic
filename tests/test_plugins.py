from __future__ import annotations

import contextlib
from typing import Any, Generator

from pydantic_core import ValidationError

from pydantic import BaseModel
from pydantic.plugin import PydanticPluginProtocol, ValidateJsonHandlerProtocol, ValidatePythonHandlerProtocol
from pydantic.plugin._loader import _plugins


@contextlib.contextmanager
def install_plugin(plugin: PydanticPluginProtocol) -> Generator[None, None, None]:
    _plugins[plugin.__class__.__qualname__] = plugin
    yield
    _plugins.clear()


def test_on_validate_json_on_success() -> None:
    class CustomOnValidateJson(ValidateJsonHandlerProtocol):
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

        def on_success(self, result: Any) -> None:
            assert isinstance(result, Model)

    class CustomPlugin(PydanticPluginProtocol):
        def new_schema_validator(self, schema, config, plugin_settings):
            assert config == {'title': 'Model'}
            assert plugin_settings == {'observe': 'all'}
            return None, CustomOnValidateJson(), None

    plugin = CustomPlugin()
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        Model.model_validate({'a': 1}) == {'a': 1}
        Model.model_validate_json('{"a": 1}') == {'a': 1}


def test_on_validate_json_on_error() -> None:
    class CustomOnValidateJson:
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

    class Plugin(PydanticPluginProtocol):
        def new_schema_validator(self, schema, config, plugin_settings):
            assert config == {'title': 'Model'}
            assert plugin_settings == {'observe': 'all'}
            return None, CustomOnValidateJson(), None

    plugin = Plugin()
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        Model.model_validate({'a': 1}) == {'a': 1}
        with contextlib.suppress(ValidationError):
            Model.model_validate_json('{"a": "potato"}')


def test_on_validate_python_on_success() -> None:
    class CustomOnValidatePython(ValidatePythonHandlerProtocol):
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

        def on_success(self, result: Any) -> None:
            assert isinstance(result, Model)

    class Plugin:
        def new_schema_validator(self, schema, config, plugin_settings):
            assert config == {'title': 'Model'}
            assert plugin_settings == {'observe': 'all'}
            return CustomOnValidatePython(), None, None

    plugin = Plugin()
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        Model.model_validate({'a': 1}) == {'a': 1}
        Model.model_validate_json('{"a": 1}') == {'a': 1}


def test_on_validate_python_on_error() -> None:
    class CustomOnValidatePython(ValidatePythonHandlerProtocol):
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

    class Plugin(PydanticPluginProtocol):
        def new_schema_validator(self, schema, config, plugin_settings):
            assert config == {'title': 'Model'}
            assert plugin_settings == {'observe': 'all'}
            return CustomOnValidatePython(), None, None

    plugin = Plugin()
    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

        with contextlib.suppress(ValidationError):
            Model.model_validate({'a': 'potato'})
        Model.model_validate_json('{"a": 1}') == {'a': 1}
