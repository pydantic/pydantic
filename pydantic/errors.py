from __future__ import annotations as _annotations

__all__ = 'PydanticUserError', 'PydanticSchemaGenerationError'


class PydanticUserError(TypeError):
    """
    Error caused by incorrect use of pydantic
    """

    def __init__(self, type: str, message: str):
        super().__init__(message)
        self.type = type
        self.message = message

    def __str__(self) -> str:
        return f'PydanticUserError(type={self.type}, message={self.message})'


class PydanticUndefinedAnnotation(NameError):
    """
    Error occurs when annotations are not yet defined
    """

    def __init__(self, type: str, message: str):
        super().__init__(message)
        self.type = type
        self.message = message

    def __str__(self) -> str:
        return f'PydanticUndefinedAnnotation(type={self.type}, message={self.message})'


class PydanticSchemaGenerationError(PydanticUserError):
    """
    Error occurs when schema has not been generated correctly.
    """

    def __init__(self, type: str, message: str):
        super().__init__(type, message)
        self.type = type
        self.message = message

    def __str__(self) -> str:
        return f'PydanticSchemaGenerationError(type={self.type}, message={self.message})'
