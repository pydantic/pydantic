import importlib
import os

import pytest

import pydantic

try:
    from mypy import api as mypy_api
    from mypy.version import __version__ as mypy_version

    from pydantic.mypy import parse_mypy_version
except ImportError:
    mypy_api = None
    mypy_version = None
    parse_mypy_version = lambda _: (0,)  # noqa: E731


try:
    import dotenv
except ImportError:
    dotenv = None


def test_imports() -> None:
    from pydantic.v1 import BaseModel, dataclasses  # noqa: F401


def test_imports_from_modules() -> None:
    """That specific objects can be imported from modules directly through the
    ``v1`` namespace."""
    from pydantic.v1.fields import ModelField  # noqa: F401
    from pydantic.v1.generics import GenericModel  # noqa: F401
    from pydantic.v1.validators import bool_validator  # noqa: F401


@pytest.mark.parametrize(
    ('module_name'),
    [
        (
            module_name
            # mypy required for importing the `mypy.py` module.
            if module_name != 'mypy.py'
            else pytest.param(
                module_name,
                marks=pytest.mark.skipif(not (dotenv and mypy_api), reason='dotenv or mypy are not installed'),
            )
        )
        for module_name in os.listdir(pydantic.__path__[0])
        if not (module_name.startswith('_') or not module_name.endswith('.py') or module_name == 'v1.py')
    ],
)
def test_can_import_modules_from_v1(module_name: str) -> None:
    """That imports from any module in pydantic can be imported through
    ``pydantic.v1.<module>``"""
    module_name = module_name[:-3]

    _ = importlib.import_module(f'pydantic.v1.{module_name}')
