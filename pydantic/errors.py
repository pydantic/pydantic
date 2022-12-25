from __future__ import annotations as _annotations

__all__ = 'PydanticUserError', 'PydanticSchemaGenerationError'


class PydanticErrorMixin:
    """
    Pydantic Error Mixin for common functions
    """

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(type="{self.type}", message="{self.message}")'

    def __repr__(self) -> str:
        return self.__str__()

    def init_variables(self, type: str, message: str) -> None:
        self.type = type
        self.message = message


class PydanticUserError(PydanticErrorMixin, TypeError):
    """
    Error caused by incorrect use of Pydantic
    """

    def __init__(self, type: str, message: str) -> None:
        super(TypeError, self).__init__(message)
        self.init_variables(type, message)


class PydanticUndefinedAnnotation(PydanticErrorMixin, NameError):
    """
    Error occurs when annotations are not yet defined
    """

    def __init__(self, type: str, message: str) -> None:
        super(NameError, self).__init__(message)
        self.init_variables(type, message)


class PydanticSchemaGenerationError(PydanticUserError):
    """
    Error occurs when schema has not been generated correctly.
    """

    def __init__(self, type: str, message: str) -> None:
        super(PydanticUserError, self).__init__(type, message)
        self.init_variables(type, message)
