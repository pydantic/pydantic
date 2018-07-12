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

    Environment variables must be upper case. Eg. to override foobar, `export APP_FOOBAR="whatever"`.

    This is useful in production for secrets you do not wish to save in code, it places nicely with docker(-compose),
    Heroku and any 12 factor app design.
    """

    def __init__(self, **values):
        values = {
            **self._substitute_environ(),
            **values,
        }
        super().__init__(**values)

    def _substitute_environ(self):
        """
        Substitute environment variables into values.
        """
        d = {}
        for field in self.__fields__.values():
            if field.alt_alias:
                env_name = field.alias
            else:
                env_name = self.__config__.env_prefix + field.name.upper()
            env_var = os.getenv(env_name, None)
            if env_var:
                if _complex_field(field):
                    try:
                        env_var = json.loads(env_var)
                    except ValueError as e:
                        raise SettingsError(f'error parsing JSON for "{env_name}"') from e
                d[field.alias] = env_var
        return d

    class Config:
        env_prefix = 'APP_'
        validate_all = True
        ignore_extra = False
        arbitrary_types_allowed = True
