"""Container union workloads for JSON validation and PGO training."""


class _TaggedPayload:
    __slots__ = '__dict__', '__pydantic_extra__', '__pydantic_fields_set__', '__pydantic_private__'

    kind: str
    values: list[int]
