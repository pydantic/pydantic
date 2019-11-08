import os
import warnings
from typing import Any, Dict, Iterable, Mapping, Optional

from .fields import ModelField
from .main import BaseModel, Extra
from .typing import display_as_type
from .utils import deep_update


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
        return deep_update(self._build_environ(), init_kwargs)

    def _build_environ(self) -> Dict[str, Optional[str]]:
        """
        Build environment variables suitable for passing to the Model.
        """
        d: Dict[str, Optional[str]] = {}

        if self.__config__.case_sensitive:
            env_vars: Mapping[str, str] = os.environ
        else:
            env_vars = {k.lower(): v for k, v in os.environ.items()}

        for field in self.__fields__.values():
            env_val: Optional[str] = None
            for env_name in field.field_info.extra['env_names']:
                env_val = env_vars.get(env_name)
                if env_val is not None:
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
            env_names: Iterable[str]
            env = field.field_info.extra.pop('env', None)
            if env is None:
                if field.has_alias:
                    warnings.warn(
                        'aliases are no longer used by BaseSettings to define which environment variables to read. '
                        'Instead use the "env" field setting. '
                        'See https://pydantic-docs.helpmanual.io/usage/settings/#environment-variable-names',
                        FutureWarning,
                    )
                env_names = [cls.env_prefix + field.name]
            elif isinstance(env, str):
                env_names = {env}
            elif isinstance(env, (list, set, tuple)):
                env_names = env
            else:
                raise TypeError(f'invalid field env: {env!r} ({display_as_type(env)}); should be string, list or set')

            if not cls.case_sensitive:
                env_names = type(env_names)(n.lower() for n in env_names)
            field.field_info.extra['env_names'] = env_names

    __config__: Config  # type: ignore
