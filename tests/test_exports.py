import importlib
import importlib.util
import json
import platform
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
IMPORTED_PYDANTIC_CODE = """
import sys
import pydantic

modules = list(sys.modules.keys())

import json
print(json.dumps(modules))
"""


def test_import_pydantic(subprocess_run_code):
    output = subprocess_run_code(IMPORTED_PYDANTIC_CODE)
    imported_modules = json.loads(output)
    # debug(imported_modules)
    assert 'pydantic' in imported_modules
    assert 'pydantic.deprecated' not in imported_modules


# language=Python
IMPORTED_BASEMODEL_CODE = """
import sys
from pydantic import BaseModel

modules = list(sys.modules.keys())

import json
print(json.dumps(modules))
"""


def test_import_base_model(subprocess_run_code):
    output = subprocess_run_code(IMPORTED_BASEMODEL_CODE)
    imported_modules = json.loads(output)
    # debug(sorted(imported_modules))
    assert 'pydantic' in imported_modules
    assert 'pydantic.fields' not in imported_modules
    assert 'pydantic.types' not in imported_modules
    assert 'annotated_types' not in imported_modules


def test_dataclass_import(subprocess_run_code):
    @subprocess_run_code
    def run_in_subprocess():
        import pydantic

        assert pydantic.dataclasses.__name__ == 'pydantic.dataclasses'

        @pydantic.dataclasses.dataclass
        class Foo:
            a: int

        try:
            Foo('not an int')
        except ValueError:
            pass
        else:
            raise AssertionError('Should have raised a ValueError')


def test_dataclass_import2(subprocess_run_code):
    @subprocess_run_code
    def run_in_subprocess():
        import pydantic.dataclasses

        assert pydantic.dataclasses.__name__ == 'pydantic.dataclasses'

        @pydantic.dataclasses.dataclass
        class Foo:
            a: int

        try:
            Foo('not an int')
        except ValueError:
            pass
        else:
            raise AssertionError('Should have raised a ValueError')
