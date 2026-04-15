Pydantic-specific errors.

## PydanticErrorMixin

```python
PydanticErrorMixin(
    message: str, *, code: PydanticErrorCodes | None
)

```

A mixin class for common functionality shared by all Pydantic-specific errors.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `message` | | A message describing the error. | | `code` | | An optional error code from PydanticErrorCodes enum. |

Source code in `pydantic/errors.py`

```python
def __init__(self, message: str, *, code: PydanticErrorCodes | None) -> None:
    self.message = message
    self.code = code

```

## PydanticUserError

```python
PydanticUserError(
    message: str, *, code: PydanticErrorCodes | None
)

```

Bases: `PydanticErrorMixin`, `RuntimeError`

An error raised due to incorrect use of Pydantic.

Source code in `pydantic/errors.py`

```python
def __init__(self, message: str, *, code: PydanticErrorCodes | None) -> None:
    self.message = message
    self.code = code

```

## PydanticUndefinedAnnotation

```python
PydanticUndefinedAnnotation(name: str, message: str)

```

Bases: `PydanticErrorMixin`, `NameError`

A subclass of `NameError` raised when handling undefined annotations during `CoreSchema` generation.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `name` | | Name of the error. | | `message` | | Description of the error. |

Source code in `pydantic/errors.py`

```python
def __init__(self, name: str, message: str) -> None:
    self.name = name
    super().__init__(message=message, code='undefined-annotation')

```

### from_name_error

```python
from_name_error(name_error: NameError) -> Self

```

Convert a `NameError` to a `PydanticUndefinedAnnotation` error.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name_error` | `NameError` | NameError to be converted. | *required* |

Returns:

| Type | Description | | --- | --- | | `Self` | Converted PydanticUndefinedAnnotation error. |

Source code in `pydantic/errors.py`

```python
@classmethod
def from_name_error(cls, name_error: NameError) -> Self:
    """Convert a `NameError` to a `PydanticUndefinedAnnotation` error.

    Args:
        name_error: `NameError` to be converted.

    Returns:
        Converted `PydanticUndefinedAnnotation` error.
    """
    try:
        name = name_error.name  # type: ignore  # python > 3.10
    except AttributeError:
        name = re.search(r".*'(.+?)'", str(name_error)).group(1)  # type: ignore[union-attr]
    return cls(name=name, message=str(name_error))

```

## PydanticImportError

```python
PydanticImportError(message: str)

```

Bases: `PydanticErrorMixin`, `ImportError`

An error raised when an import fails due to module changes between V1 and V2.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `message` | | Description of the error. |

Source code in `pydantic/errors.py`

```python
def __init__(self, message: str) -> None:
    super().__init__(message, code='import-error')

```

## PydanticSchemaGenerationError

```python
PydanticSchemaGenerationError(message: str)

```

Bases: `PydanticUserError`

An error raised during failures to generate a `CoreSchema` for some type.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `message` | | Description of the error. |

Source code in `pydantic/errors.py`

```python
def __init__(self, message: str) -> None:
    super().__init__(message, code='schema-for-unknown-type')

```

## PydanticInvalidForJsonSchema

```python
PydanticInvalidForJsonSchema(message: str)

```

Bases: `PydanticUserError`

An error raised during failures to generate a JSON schema for some `CoreSchema`.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `message` | | Description of the error. |

Source code in `pydantic/errors.py`

```python
def __init__(self, message: str) -> None:
    super().__init__(message, code='invalid-for-json-schema')

```

## PydanticForbiddenQualifier

```python
PydanticForbiddenQualifier(
    qualifier: Qualifier, annotation: Any
)

```

Bases: `PydanticUserError`

An error raised if a forbidden type qualifier is found in a type annotation.

Source code in `pydantic/errors.py`

```python
def __init__(self, qualifier: Qualifier, annotation: Any) -> None:
    super().__init__(
        message=(
            f'The annotation {_repr.display_as_type(annotation)!r} contains the {self._qualifier_repr_map[qualifier]!r} '
            f'type qualifier, which is invalid in the context it is defined.'
        ),
        code=None,
    )

```
