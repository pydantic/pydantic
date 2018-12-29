import json
import os

from .main import BaseModel


class SettingsError(ValueError):
    pass


class BaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.

    By default environment variables must be upper case and prefixed by APP_ by default. Eg. to override foobar,
    `export APP_FOOBAR="whatever"`. To change this behaviour set Config options case_insensitive and env_prefix.

    This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose),
    Heroku and any 12 factor app design.
    """

    def __init__(self, **values):
        super().__init__(**self._build_values(values))

    def _build_values(self, init_kwargs):
        return {**self._build_environ(), **init_kwargs}

    def _build_environ(self):
        """
        Build environment variables suitable for passing to the Model.
        """
        d = {}

        if self.__config__.case_insensitive:
            env_vars = {k.lower(): v for k, v in os.environ.items()}
        else:
            env_vars = os.environ

        for field in self.__fields__.values():
            if field.has_alias:
                env_name = field.alias
            else:
                env_name = self.__config__.env_prefix + field.name.upper()

            env_name_ = env_name.lower() if self.__config__.case_insensitive else env_name
            env_val = env_vars.get(env_name_, None)

            if env_val:
                if field.is_complex():
                    try:
                        env_val = json.loads(env_val)
                    except ValueError as e:
                        raise SettingsError(f'error parsing JSON for "{env_name}"') from e
                d[field.alias] = env_val
        return d

    class Config:
        env_prefix = 'APP_'
        validate_all = True
        ignore_extra = False
        arbitrary_types_allowed = True
        case_insensitive = False
