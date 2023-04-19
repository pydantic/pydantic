import importlib

import pytest

from pydantic._migration import DEPRECATED_MOVED_IN_V2, MOVED_IN_V2, REMOVED_IN_V2
from pydantic.errors import PydanticImportError


def import_from(dotted_path: str):
    module, obj_name = dotted_path.rsplit('.', 1)
    module = importlib.import_module(module)
    return getattr(module, obj_name)


@pytest.mark.filterwarnings('ignore::UserWarning')
@pytest.mark.parametrize('module', MOVED_IN_V2.keys())
def test_moved_on_v2(module: str):
    import_from(module)


@pytest.mark.parametrize('module', DEPRECATED_MOVED_IN_V2.keys())
def test_moved_but_not_warn_on_v2(module: str):
    import_from(module)


@pytest.mark.parametrize('module', REMOVED_IN_V2)
def test_removed_on_v2(module: str):
    with pytest.raises(PydanticImportError, match=f'`{module}` has been removed in V2.'):
        import_from(module)
        assert False, f'{module} should not be importable'
