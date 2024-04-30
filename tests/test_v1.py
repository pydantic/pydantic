import importlib
import os

import pydantic


def test_imports() -> None:
    from pydantic.v1 import BaseModel, dataclasses  # noqa: F401


def test_imports_from_modules() -> None:
    """That specific objects can be imported from modules directly through the
    ``v1`` namespace."""
    from pydantic.v1.fields import ModelField  # noqa: F401
    from pydantic.v1.generics import GenericModel  # noqa: F401
    from pydantic.v1.validators import bool_validator  # noqa: F401


def test_can_import_modules_from_v1() -> None:
    """That imports from any module in pydantic can be imported through
    ``pydantic.v1.<module>``"""
    for module_fname in os.listdir(pydantic.__path__[0]):
        if module_fname.startswith('_') or not module_fname.endswith('.py') or module_fname == 'v1.py':
            continue
        module_name = module_fname[:-3]

        _ = importlib.import_module(f'pydantic.v1.{module_name}')
