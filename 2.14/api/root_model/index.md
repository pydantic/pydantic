RootModel class and type definitions.

## RootModel

```python
RootModel(
    root: RootModelRootType = PydanticUndefined, **data
)

```

Bases: `BaseModel`, `Generic[RootModelRootType]`

Usage Documentation

[`RootModel` and Custom Root Types](../../concepts/models/#rootmodel-and-custom-root-types)

A Pydantic `BaseModel` for the root object of the model.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `root` | `RootModelRootType` | The root object of the model. | | `__pydantic_root_model__` | | Whether the model is a RootModel. | | `__pydantic_private__` | | Private fields in the model. | | `__pydantic_extra__` | | Extra fields in the model. |

Source code in `pydantic/root_model.py`

```python
def __init__(self, /, root: RootModelRootType = PydanticUndefined, **data) -> None:  # type: ignore
    __tracebackhide__ = True
    if data:
        if root is not PydanticUndefined:
            raise ValueError(
                '"RootModel.__init__" accepts either a single positional argument or arbitrary keyword arguments'
            )
        root = data  # type: ignore
    self.__pydantic_validator__.validate_python(root, self_instance=self)

```

### model_construct

```python
model_construct(
    root: RootModelRootType,
    _fields_set: set[str] | None = None,
) -> Self

```

Create a new model using the provided root object and update fields set.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `root` | `RootModelRootType` | The root object of the model. | *required* | | `_fields_set` | `set[str] | None` | The set of fields to be updated. | `None` |

Returns:

| Type | Description | | --- | --- | | `Self` | The new model. |

Raises:

| Type | Description | | --- | --- | | `NotImplemented` | If the model is not a subclass of RootModel. |

Source code in `pydantic/root_model.py`

```python
@classmethod
def model_construct(cls, root: RootModelRootType, _fields_set: set[str] | None = None) -> Self:  # type: ignore
    """Create a new model using the provided root object and update fields set.

    Args:
        root: The root object of the model.
        _fields_set: The set of fields to be updated.

    Returns:
        The new model.

    Raises:
        NotImplemented: If the model is not a subclass of `RootModel`.
    """
    return super().model_construct(root=root, _fields_set=_fields_set)

```

### model_dump

```python
model_dump(
    *,
    mode: Literal["json", "python"] | str = "python",
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: (
        bool | Literal["none", "warn", "error"]
    ) = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    polymorphic_serialization: bool | None = None
) -> Any

```

Usage Documentation

[`model_dump`](../../concepts/serialization/#python-mode)

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `mode` | `Literal['json', 'python'] | str` | The mode in which to_python should run. If mode is 'json', the output will only contain JSON serializable types. If mode is 'python', the output may contain non-JSON-serializable Python objects. | `'python'` | | `include` | `IncEx | None` | A set of fields to include in the output. | `None` | | `exclude` | `IncEx | None` | A set of fields to exclude from the output. | `None` | | `context` | `Any | None` | Additional context to pass to the serializer. | `None` | | `by_alias` | `bool | None` | Whether to use the field's alias in the dictionary key if defined. | `None` | | `exclude_unset` | `bool` | Whether to exclude fields that have not been explicitly set. | `False` | | `exclude_defaults` | `bool` | Whether to exclude fields that are set to their default value. | `False` | | `exclude_none` | `bool` | Whether to exclude fields that have a value of None. | `False` | | `exclude_computed_fields` | `bool` | Whether to exclude computed fields. While this can be useful for round-tripping, it is usually recommended to use the dedicated round_trip parameter instead. | `False` | | `round_trip` | `bool` | If True, dumped values should be valid as input for non-idempotent types such as Json[T]. | `False` | | `warnings` | `bool | Literal['none', 'warn', 'error']` | How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors, "error" raises a PydanticSerializationError. | `True` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered. If not provided, a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `polymorphic_serialization` | `bool | None` | Whether to use model and dataclass polymorphic serialization for this call. | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | A dictionary representation of the model. |

Source code in `pydantic/root_model.py`

```python
def model_dump(  # type: ignore
    self,
    *,
    mode: Literal['json', 'python'] | str = 'python',
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal['none', 'warn', 'error'] = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    polymorphic_serialization: bool | None = None,
) -> Any:
    """!!! abstract "Usage Documentation"
        [`model_dump`](../concepts/serialization.md#python-mode)

    Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

    Args:
        mode: The mode in which `to_python` should run.
            If mode is 'json', the output will only contain JSON serializable types.
            If mode is 'python', the output may contain non-JSON-serializable Python objects.
        include: A set of fields to include in the output.
        exclude: A set of fields to exclude from the output.
        context: Additional context to pass to the serializer.
        by_alias: Whether to use the field's alias in the dictionary key if defined.
        exclude_unset: Whether to exclude fields that have not been explicitly set.
        exclude_defaults: Whether to exclude fields that are set to their default value.
        exclude_none: Whether to exclude fields that have a value of `None`.
        exclude_computed_fields: Whether to exclude computed fields.
            While this can be useful for round-tripping, it is usually recommended to use the dedicated
            `round_trip` parameter instead.
        round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
        warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
            "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
        fallback: A function to call when an unknown value is encountered. If not provided,
            a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
        serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

    Returns:
        A dictionary representation of the model.
    """
    ...

```
