import os
import warnings
from pathlib import Path
from typing import AbstractSet, Any, Dict, List, Mapping, Optional, Union

from .fields import ModelField
from .main import BaseModel, Extra
from .typing import display_as_type
from .utils import deep_update, sequence_like

env_file_sentinel = str(object())


class SettingsError(ValueError):
    pass


class BaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.

    This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose),
    Heroku and any 12 factor app design.
    """

    def __init__(
        __pydantic_self__,
        _env_file: Union[Path, str, None] = env_file_sentinel,
        _env_file_encoding: Optional[str] = None,
        **values: Any,
    ) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        super().__init__(
            **__pydantic_self__._build_values(values, _env_file=_env_file, _env_file_encoding=_env_file_encoding)
        )

    def _build_values(
        self,
        init_kwargs: Dict[str, Any],
        _env_file: Union[Path, str, None] = None,
        _env_file_encoding: Optional[str] = None,
    ) -> Dict[str, Any]:
        return deep_update(self._build_environ(_env_file, _env_file_encoding), init_kwargs)

    def _build_environ(
        self, _env_file: Union[Path, str, None] = None, _env_file_encoding: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Build environment variables suitable for passing to the Model.
        """
        d: Dict[str, Optional[str]] = {}

        if self.__config__.case_sensitive:
            env_vars: Mapping[str, Optional[str]] = os.environ
        else:
            env_vars = {k.lower(): v for k, v in os.environ.items()}

        env_file = _env_file if _env_file != env_file_sentinel else self.__config__.env_file
        env_file_encoding = _env_file_encoding if _env_file_encoding is not None else self.__config__.env_file_encoding
        if env_file is not None:
            env_path = Path(env_file)
            if env_path.is_file():
                env_vars = {
                    **read_env_file(
                        env_path, encoding=env_file_encoding, case_sensitive=self.__config__.case_sensitive
                    ),
                    **env_vars,
                }

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
        env_file = None
        env_file_encoding = None
        validate_all = True
        extra = Extra.forbid
        arbitrary_types_allowed = True
        case_sensitive = False

        @classmethod
        def prepare_field(cls, field: ModelField) -> None:
            env_names: Union[List[str], AbstractSet[str]]
            env = field.field_info.extra.get('env')
            if env is None:
                if field.has_alias:
                    warnings.warn(
                        'aliases are no longer used by BaseSettings to define which environment variables to read. '
                        'Instead use the "env" field setting. '
                        'See https://pydantic-docs.helpmanual.io/usage/settings/#environment-variable-names',
                        FutureWarning,
                    )
                env_names = {cls.env_prefix + field.name}
            elif isinstance(env, str):
                env_names = {env}
            elif isinstance(env, (set, frozenset)):
                env_names = env
            elif sequence_like(env):
                env_names = list(env)
            else:
                raise TypeError(f'invalid field env: {env!r} ({display_as_type(env)}); should be string, list or set')

            if not cls.case_sensitive:
                env_names = env_names.__class__(n.lower() for n in env_names)
            field.field_info.extra['env_names'] = env_names

    __config__: Config  # type: ignore


def read_env_file(file_path: Path, *, encoding: str = None, case_sensitive: bool = False) -> Dict[str, Optional[str]]:
    try:
        from dotenv import dotenv_values
    except ImportError as e:
        raise ImportError('python-dotenv is not installed, run `pip install pydantic[dotenv]`') from e

    file_vars: Dict[str, Optional[str]] = dotenv_values(file_path, encoding=encoding or 'utf8')
    if not case_sensitive:
        return {k.lower(): v for k, v in file_vars.items()}
    else:
        return file_vars
