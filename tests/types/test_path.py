from pathlib import Path

from pydantic import BaseModel


def test_path_default():
    """Regression test for https://github.com/pydantic/pydantic/issues/13318."""

    class Config(BaseModel):
        path: Path = Path('config.toml')

    assert Config.model_json_schema()['properties']['path']['default'] == 'config.toml'
