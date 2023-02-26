import warnings
from types import ModuleType
from typing import Any, Tuple

from pydantic_core import ValidationError


class V2MigrationRemovedException(Exception):
    ...


class V2MigrationMovedWarning(DeprecationWarning):
    ...


class V2MigrationRenamedWarning(DeprecationWarning):
    ...


class V2MigrationSuperseded(Exception):
    ...


V2_MIGRATION_MAPPING = {
    # Case: Removed
    'pydantic.Required': V2MigrationRemovedException('pydantic.Required has been removed in favour of ...'),
    'pydantic.fields.Required': V2MigrationRemovedException('pydantic.Required has been removed in favour of ...'),
    # Case: Moved path
    'pydantic.error_wrappers.ValidationError': (
        'ValidationError has been moved from pydantic.error_wrappers during the migration to V2\n'
        'Please use either:\n'
        'from pydantic import ValidationError\n'
        'or\n'
        'from pydantic_core import ValidationError',
        ValidationError,
    )
    # Case: Renamed object
    # Case: Superseded
}


def patch_importlib_with_migration_info(importlib: ModuleType) -> None:
    __handle_fromlist = importlib._bootstrap._handle_fromlist

    def _handle_fromlist_override(
        module: ModuleType, fromlist: Tuple[str, ...], import_: Any, *, recursive: bool = False
    ) -> Any:
        inform(f"{module.__name__}.{'.'.join(fromlist)}")

        return __handle_fromlist(module, fromlist, import_, recursive=recursive)

    importlib._bootstrap._handle_fromlist = _handle_fromlist_override


def inform(object_import: str) -> Any:
    exception = V2_MIGRATION_MAPPING.get(object_import)
    if isinstance(exception, Exception):
        raise exception
    if isinstance(exception, tuple):
        warnings.warn(exception[0].strip(), V2MigrationMovedWarning)
        return exception[1]


def getattr(module_name: str, name: str) -> Any:
    obj = inform(f'{module_name}.{name}')
    if obj:
        return obj
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
