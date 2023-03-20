from __future__ import annotations as _annotations

__all__ = (
    'PydanticUserError',
    'PydanticSchemaGenerationError',
    'PydanticUndefinedAnnotation',
    'PydanticInvalidForJsonSchema',
)


class PydanticErrorMixin:
    """
    Pydantic Error Mixin for common functions
    """

    def __init__(self, code: str, *, message: str | None = None) -> None:
        self.code = code
        self.message = message


class PydanticUserError(PydanticErrorMixin, TypeError):
    """
    Error caused by incorrect use of Pydantic
    """

    pass


class PydanticUndefinedAnnotation(PydanticErrorMixin, NameError):
    """
    Error occurs when annotations are not yet defined
    """

    def __init__(self, name: str, *, message: str | None = None) -> None:
        self.name = name
        super().__init__(code=name, message=message)


class PydanticSchemaGenerationError(PydanticUserError):
    """
    Error occurs when schema has not been generated correctly.
    """

    pass


class PydanticInvalidForJsonSchema(PydanticUserError):
    """
    Error raised when a type from a CoreSchema is not compatible with JSON schema generation
    """

    pass
