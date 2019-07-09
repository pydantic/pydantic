import json
import os
from typing import Any, Dict, Optional, cast

from .main import BaseModel, Extra


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

    def __init__(__pydantic_self__, **values: Any) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        super().__init__(**__pydantic_self__._build_values(values))

    def _build_values(self, init_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        return {**self._build_environ(), **init_kwargs}

    def _build_environ(self) -> Dict[str, Optional[str]]:
        """
        Build environment variables suitable for passing to the Model.
        """
        d: Dict[str, Optional[str]] = {}

        if self.__config__.case_insensitive:
            env_vars = {k.lower(): v for k, v in os.environ.items()}
        else:
            env_vars = cast(Dict[str, str], os.environ)

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
        extra = Extra.forbid
        arbitrary_types_allowed = True
        case_insensitive = False

    __config__: Config  # type: ignore
