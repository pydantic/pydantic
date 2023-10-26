from pydantic import BaseModel


class MyModel(BaseModel):
    x: int


m = MyModel(x='10')
if m.x != 10:
    raise ValueError('m.x should be 10')

log = []


class ValidatePythonHandler:
    def on_enter(self, *args, **kwargs) -> None:
        log.append(f'on_enter args={args} kwargs={kwargs}')

    def on_success(self, result) -> None:
        log.append(f'on_success result={result}')

    def on_error(self, error) -> None:
        log.append(f'on_error error={error}')


class Plugin:
    def new_schema_validator(self, schema, schema_type, schema_type_path, schema_kind, config, plugin_settings):
        return ValidatePythonHandler(), None, None


plugin = Plugin()
