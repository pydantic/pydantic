import json
import os

from .fields import Shape
from .main import BaseModel


class SettingsError(ValueError):
    pass


def _complex_field(field):
    try:
        return field and (field.shape != Shape.SINGLETON or issubclass(field.type_, (BaseModel, list, set, dict)))
    except TypeError:
        # if field.type_ is not a class
        return False


class BaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.

    Environment variables must be upper case and prefixed by APP_ by default. Eg. to override foobar,
    `export APP_FOOBAR="whatever"`. To change this behaviour set Config options case_insensitive and
    env_prefix.

    This is useful in production for secrets you do not wish to save in code, it places nicely with docker(-compose),
    Heroku and any 12 factor app design.
    """

    def __init__(self, **values):
        values = {**self._substitute_environ(), **values}
        super().__init__(**values)

    def _substitute_environ(self):
        """
        Substitute environment variables into values.
        """
        d = {}

        if self.__config__.case_insensitive:
            env_vars = {k.lower(): v for (k, v) in os.environ.items()}
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
                if _complex_field(field):
                    try:
                        env_val = json.loads(env_val)
                    except ValueError as e:
                        raise SettingsError(f'error parsing JSON for "{env_name}"') from e
                d[field.alias] = env_val
        return d

    class Config:
        env_prefix = "APP_"
        validate_all = True
        ignore_extra = False
        arbitrary_types_allowed = True
        case_insensitive = False
