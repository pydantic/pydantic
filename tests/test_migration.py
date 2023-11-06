import importlib

import pytest

from pydantic._migration import DEPRECATED_MOVED_IN_V2, MOVED_IN_V2, REDIRECT_TO_V1, REMOVED_IN_V2, getattr_migration
from pydantic.errors import PydanticImportError


def import_from(dotted_path: str):
    if ':' in dotted_path:
        module, obj_name = dotted_path.rsplit(':', 1)
        module = importlib.import_module(module)
        return getattr(module, obj_name)
    else:
        return importlib.import_module(dotted_path)


@pytest.mark.filterwarnings('ignore::UserWarning')
@pytest.mark.parametrize('module', MOVED_IN_V2.keys())
def test_moved_on_v2(module: str):
    import_from(module)


@pytest.mark.parametrize('module', DEPRECATED_MOVED_IN_V2.keys())
def test_moved_but_not_warn_on_v2(module: str):
    import_from(module)


@pytest.mark.filterwarnings('ignore::UserWarning')
@pytest.mark.parametrize('module', REDIRECT_TO_V1.keys())
def test_redirect_to_v1(module: str):
    import_from(module)


@pytest.mark.parametrize('module', REMOVED_IN_V2)
def test_removed_on_v2(module: str):
    with pytest.raises(PydanticImportError, match=f'`{module}` has been removed in V2.'):
        import_from(module)
        assert False, f'{module} should not be importable'


def test_base_settings_removed():
    with pytest.raises(PydanticImportError, match='`BaseSettings` has been moved to the `pydantic-settings` package. '):
        import_from('pydantic:BaseSettings')
        assert False, 'pydantic:BaseSettings should not be importable'


def test_getattr_migration():
    get_attr = getattr_migration(__name__)

    assert callable(get_attr('test_getattr_migration')) is True

    with pytest.raises(AttributeError, match="module 'tests.test_migration' has no attribute 'foo'"):
        get_attr('foo')
