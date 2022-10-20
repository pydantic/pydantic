from __future__ import annotations as _annotations

__all__ = 'PydanticUserError', 'PydanticSchemaGenerationError'


class PydanticUserError(TypeError):
    """
    Error caused by incorrect use of pydantic
    """


class PydanticSchemaGenerationError(PydanticUserError):
    pass
