from __future__ import annotations as _annotations

from typing import Optional

__all__ = 'PydanticUserError', 'PydanticSchemaGenerationError'


class PydanticErrorMixin:
    """
    Pydantic Error Mixin for common functions
    """

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(code={self.code!r}, message={self.message!r})'

    def __repr__(self) -> str:
        return self.__str__()

    def __init__(self, code: str, *, message: Optional[str] = None) -> None:
        self.code = code
        self.message = message
        super().__init__()


class PydanticUserError(PydanticErrorMixin, TypeError):
    """
    Error caused by incorrect use of Pydantic
    """

    pass


class PydanticUndefinedAnnotation(PydanticErrorMixin, NameError):
    """
    Error occurs when annotations are not yet defined
    """

    pass


class PydanticSchemaGenerationError(PydanticUserError):
    """
    Error occurs when schema has not been generated correctly.
    """

    pass
