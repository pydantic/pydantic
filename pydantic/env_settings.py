import os
from typing import Any, Dict, Iterable, Optional, cast

from .fields import ModelField
from .main import BaseModel, Extra
from .typing import display_as_type


class SettingsError(ValueError):
    pass


class BaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.

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

        if self.__config__.case_sensitive:
            env_vars = cast(Dict[str, str], os.environ)
        else:
            env_vars = {k.lower(): v for k, v in os.environ.items()}

        for field in self.__fields__.values():
            env_val: Optional[str] = None
            for env_name in field.field_info.extra['env_names']:  # type: ignore
                env_name_ = env_name if self.__config__.case_sensitive else env_name.lower()
                try:
                    env_val = env_vars[env_name_]
                except KeyError:
                    pass
                else:
                    break

            if env_val is None:
                continue

            if field.is_complex():
                try:
                    env_val = self.__config__.json_loads(env_val)  # type: ignore
                except ValueError as e:
                    raise SettingsError(f'error parsing JSON for "{env_name}"') from e
            d[field.alias] = env_val
        return d

    class Config:
        env_prefix = ''
        validate_all = True
        extra = Extra.forbid
        arbitrary_types_allowed = True
        case_sensitive = False

        @classmethod
        def prepare_field(cls, field: ModelField) -> None:
            if not field.field_info:
                return

            env_names: Iterable[str]
            env = field.field_info.extra.pop('env', None)
            if isinstance(env, str):
                env_names = {env}
            elif isinstance(env, (list, set, tuple)):
                env_names = env
            elif env is not None:
                raise TypeError(f'invalid field env: {env!r} ({display_as_type(env)}); should be string, list or set')
            else:
                env_names = [cls.env_prefix + field.name]

            field.field_info.extra['env_names'] = env_names

    __config__: Config  # type: ignore
