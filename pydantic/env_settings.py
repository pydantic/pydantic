import os
import warnings
from pathlib import Path
from typing import AbstractSet, Any, Callable, ClassVar, Dict, List, MutableMapping, Optional, Tuple, Type, Union

from .config import BaseConfig, Extra
from .fields import ModelField
from .main import BaseModel
from .typing import StrPath, display_as_type, get_origin, is_union_origin
from .utils import deep_update, path_type, sequence_like

env_file_sentinel = str(object())

SettingsSourceCallable = Callable[['BaseSettings'], Dict[str, Any]]
MultiDotenvType = Union[List[StrPath], Tuple[StrPath, ...]]
DotenvType = Union[StrPath, MultiDotenvType]


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
        _env_file: Optional[DotenvType] = env_file_sentinel,
        _env_file_encoding: Optional[str] = None,
        _secrets_dir: Optional[StrPath] = None,
        **values: Any,
    ) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        super().__init__(
            **__pydantic_self__._build_values(
                values, _env_file=_env_file, _env_file_encoding=_env_file_encoding, _secrets_dir=_secrets_dir
            )
        )

    def _build_values(
        self,
        init_kwargs: Dict[str, Any],
        _env_file: Optional[DotenvType] = None,
        _env_file_encoding: Optional[str] = None,
        _secrets_dir: Optional[StrPath] = None,
    ) -> Dict[str, Any]:
        # Configure built-in sources
        init_settings = InitSettingsSource(init_kwargs=init_kwargs)
        env_settings = EnvSettingsSource(
            env_file=(_env_file if _env_file != env_file_sentinel else self.__config__.env_file),
            env_file_encoding=(
                _env_file_encoding if _env_file_encoding is not None else self.__config__.env_file_encoding
            ),
        )
        file_secret_settings = SecretsSettingsSource(secrets_dir=_secrets_dir or self.__config__.secrets_dir)
        # Provide a hook to set built-in sources priority and add / remove sources
        sources = self.__config__.customise_sources(
            init_settings=init_settings, env_settings=env_settings, file_secret_settings=file_secret_settings
        )
        if sources:
            return deep_update(*reversed([source(self) for source in sources]))
        else:
            # no one should mean to do this, but I think returning an empty dict is marginally preferable
            # to an informative error and much better than a confusing error
            return {}

    class Config(BaseConfig):
        env_prefix = ''
        env_file = None
        env_file_encoding = None
        secrets_dir = None
        validate_all = True
        extra = Extra.forbid
        arbitrary_types_allowed = True
        case_sensitive = False

        @classmethod
        def prepare_field(cls, field: ModelField) -> None:
            env_names: Union[List[str], AbstractSet[str]]
            field_info_from_config = cls.get_field_info(field.name)

            env = field_info_from_config.get('env') or field.field_info.extra.get('env')
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

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return init_settings, env_settings, file_secret_settings

    # populated by the metaclass using the Config class defined above, annotated here to help IDEs only
    __config__: ClassVar[Type[Config]]


class InitSettingsSource:
    __slots__ = ('init_kwargs',)

    def __init__(self, init_kwargs: Dict[str, Any]):
        self.init_kwargs = init_kwargs

    def __call__(self, settings: BaseSettings) -> Dict[str, Any]:
        return self.init_kwargs

    def __repr__(self) -> str:
        return f'InitSettingsSource(init_kwargs={self.init_kwargs!r})'


class EnvSettingsSource:
    __slots__ = ('env_file', 'env_file_encoding')

    def __init__(self, env_file: Optional[DotenvType], env_file_encoding: Optional[str]):
        self.env_file: Optional[DotenvType] = env_file
        self.env_file_encoding: Optional[str] = env_file_encoding

    @staticmethod
    def _read_process_env_vars(case_sensitive: bool) -> MutableMapping[str, str]:
        if case_sensitive:
            return os.environ
        else:
            return {k.lower(): v for k, v in os.environ.items()}

    @staticmethod
    def _read_dotenv_vars(
        env_files: Optional[DotenvType], env_file_encoding: Optional[str], case_sensitive: bool
    ) -> Dict[str, Optional[str]]:
        def read_dotenv_file(env_file: StrPath) -> Dict[str, Optional[str]]:
            env_path = Path(env_file).expanduser()
            if not env_path.is_file():
                return {}

            return read_env_file(env_path, encoding=env_file_encoding, case_sensitive=case_sensitive)

        if env_files is None:
            return {}
        elif isinstance(env_files, (str, os.PathLike)):
            return read_dotenv_file(env_files)
        elif isinstance(env_files, (tuple, list)):
            return {k: v for path in reversed(env_files) for k, v in read_dotenv_file(path).items()}
        else:
            raise TypeError(f'expected str, os.PathLike, list or tuple object, not {type(env_files).__name__}')

    def __call__(self, settings: BaseSettings) -> Dict[str, Any]:
        """
        Build environment variables suitable for passing to the Model.
        """
        d: Dict[str, Optional[str]] = {}

        case_sensitive = settings.__config__.case_sensitive
        process_env_vars = self._read_process_env_vars(case_sensitive)
        dotenv_vars = self._read_dotenv_vars(self.env_file, self.env_file_encoding, case_sensitive)
        env_vars = {**dotenv_vars, **process_env_vars}

        for field in settings.__fields__.values():
            env_val: Optional[str] = None
            for env_name in field.field_info.extra['env_names']:
                env_val = env_vars.get(env_name)
                if env_val is not None:
                    break

            if env_val is None:
                continue

            if field.is_complex():
                try:
                    env_val = settings.__config__.json_loads(env_val)
                except ValueError as e:
                    raise SettingsError(f'error parsing JSON for "{env_name}"') from e
            elif (
                is_union_origin(get_origin(field.type_))
                and field.sub_fields
                and any(f.is_complex() for f in field.sub_fields)
            ):
                try:
                    env_val = settings.__config__.json_loads(env_val)
                except ValueError:
                    pass
            d[field.alias] = env_val
        return d

    def __repr__(self) -> str:
        return f'EnvSettingsSource(env_file={self.env_file!r}, env_file_encoding={self.env_file_encoding!r})'


class SecretsSettingsSource:
    __slots__ = ('secrets_dir',)

    def __init__(self, secrets_dir: Optional[StrPath]):
        self.secrets_dir: Optional[StrPath] = secrets_dir

    def __call__(self, settings: BaseSettings) -> Dict[str, Any]:
        """
        Build fields from "secrets" files.
        """
        secrets: Dict[str, Optional[str]] = {}

        if self.secrets_dir is None:
            return secrets

        secrets_path = Path(self.secrets_dir).expanduser()

        if not secrets_path.exists():
            warnings.warn(f'directory "{secrets_path}" does not exist')
            return secrets

        if not secrets_path.is_dir():
            raise SettingsError(f'secrets_dir must reference a directory, not a {path_type(secrets_path)}')

        for field in settings.__fields__.values():
            for env_name in field.field_info.extra['env_names']:
                path = secrets_path / env_name
                if path.is_file():
                    secrets[field.alias] = path.read_text().strip()
                elif path.exists():
                    warnings.warn(
                        f'attempted to load secret file "{path}" but found a {path_type(path)} instead.',
                        stacklevel=4,
                    )

        return secrets

    def __repr__(self) -> str:
        return f'SecretsSettingsSource(secrets_dir={self.secrets_dir!r})'


def read_env_file(
    file_path: StrPath, *, encoding: str = None, case_sensitive: bool = False
) -> Dict[str, Optional[str]]:
    try:
        from dotenv import dotenv_values
    except ImportError as e:
        raise ImportError('python-dotenv is not installed, run `pip install pydantic[dotenv]`') from e

    file_vars: Dict[str, Optional[str]] = dotenv_values(file_path, encoding=encoding or 'utf8')
    if not case_sensitive:
        return {k.lower(): v for k, v in file_vars.items()}
    else:
        return file_vars
