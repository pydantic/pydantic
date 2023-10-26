from __future__ import annotations

import contextlib
from typing import Any, Generator

from pydantic_core import ValidationError

from pydantic import BaseModel, field_validator
from pydantic.plugin import (
    PydanticPluginProtocol,
    ValidateJsonHandlerProtocol,
    ValidatePythonHandlerProtocol,
    ValidateStringsHandlerProtocol,
)
from pydantic.plugin._loader import _plugins


@contextlib.contextmanager
def install_plugin(plugin: PydanticPluginProtocol) -> Generator[None, None, None]:
    _plugins[plugin.__class__.__qualname__] = plugin
    try:
        yield
    finally:
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
        def on_enter(
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
            assert error.errors(include_url=False) == [
                {
                    'input': 'potato',
                    'loc': ('a',),
                    'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
                    'type': 'int_parsing',
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
        def on_enter(
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
        def on_enter(
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

        def on_error(self, error: ValidationError) -> None:
            assert error.title == 'Model'
            assert error.errors(include_url=False) == [
                {
                    'input': 'potato',
                    'loc': ('a',),
                    'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
                    'type': 'int_parsing',
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


def test_stateful_plugin() -> None:
    stack: list[Any] = []

    class CustomOnValidatePython(ValidatePythonHandlerProtocol):
        def on_enter(
            self,
            input: Any,
            *,
            strict: bool | None = None,
            from_attributes: bool | None = None,
            context: dict[str, Any] | None = None,
            self_instance: Any | None = None,
        ) -> None:
            stack.append(input)

        def on_success(self, result: Any) -> None:
            stack.pop()

        def on_error(self, error: Exception) -> None:
            stack.pop()

        def on_exception(self, exception: Exception) -> None:
            stack.pop()

    class Plugin(PydanticPluginProtocol):
        def new_schema_validator(self, schema, config, plugin_settings):
            return CustomOnValidatePython(), None, None

    plugin = Plugin()

    class MyException(Exception):
        pass

    with install_plugin(plugin):

        class Model(BaseModel, plugin_settings={'observe': 'all'}):
            a: int

            @field_validator('a')
            def validate_a(cls, v: int) -> int:
                if v < 0:
                    raise MyException
                return v

        with contextlib.suppress(ValidationError):
            Model.model_validate({'a': 'potato'})
        assert not stack
        with contextlib.suppress(MyException):
            Model.model_validate({'a': -1})
        assert not stack
        assert Model.model_validate({'a': 1}).a == 1
        assert not stack


def test_all_handlers():
    log = []

    class Python(ValidatePythonHandlerProtocol):
        def on_enter(self, input, **kwargs) -> None:
            log.append(f'python enter input={input} kwargs={kwargs}')

        def on_success(self, result: Any) -> None:
            log.append(f'python success result={result}')

        def on_error(self, error: ValidationError) -> None:
            log.append(f'python error error={error}')

    class Json(ValidateJsonHandlerProtocol):
        def on_enter(self, input, **kwargs) -> None:
            log.append(f'json enter input={input} kwargs={kwargs}')

        def on_success(self, result: Any) -> None:
            log.append(f'json success result={result}')

        def on_error(self, error: ValidationError) -> None:
            log.append(f'json error error={error}')

    class Strings(ValidateStringsHandlerProtocol):
        def on_enter(self, input, **kwargs) -> None:
            log.append(f'strings enter input={input} kwargs={kwargs}')

        def on_success(self, result: Any) -> None:
            log.append(f'strings success result={result}')

        def on_error(self, error: ValidationError) -> None:
            log.append(f'strings error error={error}')

    class Plugin(PydanticPluginProtocol):
        def new_schema_validator(self, schema, config, plugin_settings):
            return Python(), Json(), Strings()

    plugin = Plugin()
    with install_plugin(plugin):

        class Model(BaseModel):
            a: int

        assert Model(a=1).model_dump() == {'a': 1}
        # insert_assert(log)
        assert log == ["python enter input={'a': 1} kwargs={'self_instance': Model()}", 'python success result=a=1']
        log.clear()
        assert Model.model_validate_json('{"a": 2}', context={'c': 2}).model_dump() == {'a': 2}
        # insert_assert(log)
        assert log == [
            'json enter input={"a": 2} kwargs={\'strict\': None, \'context\': {\'c\': 2}}',
            'json success result=a=2',
        ]
        log.clear()
        assert Model.model_validate_strings({'a': '3'}, strict=True, context={'c': 3}).model_dump() == {'a': 3}
        # insert_assert(log)
        assert log == [
            "strings enter input={'a': '3'} kwargs={'strict': True, 'context': {'c': 3}}",
            'strings success result=a=3',
        ]
