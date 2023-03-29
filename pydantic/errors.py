from __future__ import annotations as _annotations

import re

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

    def __init__(self, name: str, message: str | None = None) -> None:
        self.name = name
        super().__init__(code=name, message=message)

    @classmethod
    def from_name_error(cls, name_error: NameError) -> PydanticUndefinedAnnotation:
        try:
            name = name_error.name
        except AttributeError:
            name = re.search(r".*'(.+?)'", str(name_error)).group(1)  # type: ignore[union-attr]
        return cls(name=name, message=str(name_error))

    def __str__(self) -> str:
        return f'Undefined annotation: {self.message}'


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
