"""Test that the mypy plugin does not change the config type checking.

This test can most likely be removed when we drop support for the old V1 `Config` class.
"""

from pydantic import BaseModel, ConfigDict


def condition() -> bool:
    return True


class MyModel(BaseModel):
    model_config = ConfigDict(extra='ignore' if condition() else 'forbid')
