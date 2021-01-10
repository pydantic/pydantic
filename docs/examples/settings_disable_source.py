from typing import Tuple

from pydantic import BaseSettings, PostgresDsn
from pydantic.env_settings import SettingsSourceCallable


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
            # here we choose to disable entirely environ and .env file sources
            return init_settings, file_secret_settings
