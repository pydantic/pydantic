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
    "pydantic.Required": V2MigrationRemoved("pydantic.Required has been removed in favour of ..."),
    # Case: Moved path
    # Case: Renamed object
    # Case: Superseded
}

import importlib
___handle_fromlist__ = importlib._bootstrap._handle_fromlist

def _handle_fromlist_override(module, fromlist, import_, *, recursive=False):
    if exception := V2_MIGRATION_MAPPING.get(f"{module.__name__}.{'.'.join(fromlist)}"):
        raise exception
    return ___handle_fromlist__(module, fromlist, import_, recursive=recursive)

importlib._bootstrap._handle_fromlist = _handle_fromlist_override
