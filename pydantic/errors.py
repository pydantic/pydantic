from __future__ import annotations as _annotations

__all__ = 'PydanticUserError', 'PydanticSchemaGenerationError'


class PydanticUserError(TypeError):
    """
    Error caused by incorrect use of pydantic
    """


class PydanticUndefinedAnnotation(NameError):
    """
    Error occurs when annotations are not yet defined
    """


class PydanticSchemaGenerationError(PydanticUserError):
    pass
