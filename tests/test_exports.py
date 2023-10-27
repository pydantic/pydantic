import importlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

import pydantic


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_init_export():
    for name in dir(pydantic):
        getattr(pydantic, name)


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
@pytest.mark.parametrize(('attr_name', 'value'), list(pydantic._dynamic_imports.items()))
def test_public_api_dynamic_imports(attr_name, value):
    package, module_name = value
    if module_name == '__module__':
        module = importlib.import_module(attr_name, package=package)
        assert isinstance(module, ModuleType)
    else:
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


# language=Python
IMPORTED_MODULES_CODE = """
import sys
import pydantic

modules = list(sys.modules.keys())

import json
print(json.dumps(modules))
"""


def test_imported_modules(tmp_path: Path):
    py_file = tmp_path / 'test.py'
    py_file.write_text(IMPORTED_MODULES_CODE)

    output = subprocess.check_output([sys.executable, str(py_file)], cwd=tmp_path)
    imported_modules = json.loads(output)
    # debug(imported_modules)
    assert 'pydantic' in imported_modules
    assert 'pydantic.deprecated' not in imported_modules
