import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

import pydantic


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_init_export():
    pydantic_all = set(pydantic.__all__)

    exported = set()
    for name, attr in vars(pydantic).items():
        if name.startswith('_'):
            continue
        if isinstance(attr, ModuleType) and name != 'dataclasses':
            continue
        if name == 'getattr_migration':
            continue
        exported.add(name)

    assert pydantic_all == exported, "pydantic.__all__ doesn't match actual exports"


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_public_internal():
    """
    check we don't make anything from _internal public
    """
    public_internal_attributes = []
    for file in (Path(__file__).parent.parent / 'pydantic').glob('*.py'):
        if file.name != '__init__.py' and not file.name.startswith('_'):
            module_name = f'pydantic.{file.stem}'
            module = sys.modules.get(module_name)
            if module is None:
                spec = importlib.util.spec_from_file_location(module_name, str(file))
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except ImportError:
                    continue

            for name, attr in vars(module).items():
                if not name.startswith('_'):
                    attr_module = getattr(attr, '__module__', '')
                    if attr_module.startswith('pydantic._internal'):
                        public_internal_attributes.append(f'{module.__name__}:{name} from {attr_module}')

    if public_internal_attributes:
        pytest.fail('The following should not be publicly accessible:\n  ' + '\n  '.join(public_internal_attributes))
