import json
from pathlib import Path
from typing import Any, Dict, Tuple

from pydantic import BaseSettings, PostgresDsn
from pydantic.env_settings import SettingsSourceCallable


def json_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a JSON file
    at the project's root.
    """
    return json.loads(Path('config.json').read_text().strip())


class Settings(BaseSettings):
    database_dsn: PostgresDsn

    class Config:
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                env_settings,
                file_secret_settings,
                json_config_settings_source,
            )
