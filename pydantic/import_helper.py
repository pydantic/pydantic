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


def inform(current_module, obj):
    if exception := V2_MIGRATION_MAPPING.get(f"{current_module}.{obj}"):
        raise exception
