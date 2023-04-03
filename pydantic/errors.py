from __future__ import annotations as _annotations

import re

from typing_extensions import Literal

__all__ = (
    'PydanticUserError',
    'PydanticSchemaGenerationError',
    'PydanticUndefinedAnnotation',
    'PydanticInvalidForJsonSchema',
)

PYDANTIC_INTERNAL_DOCS_URL = 'https://docs.pydantic.dev/errors'
PydanticErrorCodes = Literal[
    'decorator-missing-field',
    'dataclass-not-fully-defined',
    'discriminator-no-field',
    'discriminator-alias-type',
    'discriminator-needs-literal',
    'discriminator-alias',
    'typed-dict-version',
    'model-field-overridden',
    'model-field-missing-annotation',
    'model-not-fully-defined',
    'config-both',
    'invalid-for-json-schema',
    'json-schema-already-used',
    'base-model-instantiated',
    'undefined-annotation',
    'schema-for-unknown-type',
    'create-model-field-definitions',
    'create-model-config-base',
]


class PydanticErrorMixin:
    """
    Pydantic Error Mixin for common functions
    """

    def __init__(self, message: str, *, code: PydanticErrorCodes | None) -> None:
        self.message = message
        self.code = code

    def __str__(self) -> str:
        if self.code is None:
            return self.message
        else:
            return f'{self.message}\n\nFor more information see {PYDANTIC_INTERNAL_DOCS_URL}#{self.code}'


class PydanticUserError(PydanticErrorMixin, TypeError):
    """
    Error caused by incorrect use of Pydantic
    """

    pass


class PydanticUndefinedAnnotation(PydanticErrorMixin, NameError):
    """
    Error occurs when annotations are not yet defined
    """

    def __init__(self, name: str, message: str) -> None:
        self.name = name
        super().__init__(message=message, code='undefined-annotation')

    @classmethod
    def from_name_error(cls, name_error: NameError) -> PydanticUndefinedAnnotation:
        try:
            name = name_error.name
        except AttributeError:
            name = re.search(r".*'(.+?)'", str(name_error)).group(1)  # type: ignore[union-attr]
        return cls(name=name, message=str(name_error))


class PydanticSchemaGenerationError(PydanticUserError):
    """
    Error occurs when schema has not been generated correctly.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='schema-for-unknown-type')


class PydanticInvalidForJsonSchema(PydanticUserError):
    """
    Error raised when a type from a CoreSchema is not compatible with JSON schema generation
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='invalid-for-json-schema')
