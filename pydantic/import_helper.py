from types import ModuleType
from typing import Any, Tuple


class V2MigrationRemoved(Exception):
    ...


class V2MigrationMoved(Exception):
    ...


class V2MigrationRenamed(Exception):
    ...


class V2MigrationSuperseded(Exception):
    ...


V2_MIGRATION_MAPPING = {
    # Case: Removed
    'pydantic.Required': V2MigrationRemoved('pydantic.Required has been removed in favour of ...'),
    # Case: Moved path
    # Case: Renamed object
    # Case: Superseded
}


def patch_importlib_with_migration_info(importlib: ModuleType) -> None:
    __handle_fromlist = importlib._bootstrap._handle_fromlist

    def _handle_fromlist_override(
        module: ModuleType, fromlist: Tuple[str, ...], import_: Any, *, recursive: bool = False
    ) -> Any:
        exception = V2_MIGRATION_MAPPING.get(f"{module.__name__}.{'.'.join(fromlist)}")
        if exception:
            raise exception
        return __handle_fromlist(module, fromlist, import_, recursive=recursive)

    importlib._bootstrap._handle_fromlist = _handle_fromlist_override
