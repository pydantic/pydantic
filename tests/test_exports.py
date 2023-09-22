import importlib
import importlib.util
import platform
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

    # add stuff from `pydantic._dynamic_imports` if `package` is "pydantic"
    exported.update({k for k, v in pydantic._dynamic_imports.items() if v[0] == 'pydantic'})

    assert pydantic_all == exported, "pydantic.__all__ doesn't match actual exports"


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
@pytest.mark.parametrize(('attr_name', 'value'), list(pydantic._dynamic_imports.items()))
def test_public_api_dynamic_imports(attr_name, value):
    package, module_name = value
    imported_object = getattr(importlib.import_module(module_name, package=package), attr_name)
    assert isinstance(imported_object, object)


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy' and platform.python_version_tuple() < ('3', '8'),
    reason='Produces a weird error on pypy<3.8',
)
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
