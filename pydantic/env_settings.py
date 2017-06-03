import os

from .main import BaseModel


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
        for name, field in self.__fields__.items():
            if field.alt_alias:
                env_name = field.alias
            else:
                env_name = self.config.env_prefix + field.name.upper()
            env_var = os.getenv(env_name, None)
            if env_var:
                d[field.alias] = env_var
        return d

    class Config:
        env_prefix = 'APP_'
        validate_all = True
        ignore_extra = False
