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
            return env_settings, init_settings, file_secret_settings


print(Settings(database_dsn='postgres://postgres@localhost:5432/kwargs_db'))
