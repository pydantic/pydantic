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
    include: Any = None,
    exclude: Any = None,
    context: dict[str, Any] | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: (
        bool | Literal["none", "warn", "error"]
    ) = True,
    serialize_as_any: bool = False
) -> Any

```

This method is included just to get a more accurate return type for type checkers. It is included in this `if TYPE_CHECKING:` block since no override is actually necessary.

See the documentation of `BaseModel.model_dump` for more details about the arguments.

Generally, this method will have a return type of `RootModelRootType`, assuming that `RootModelRootType` is not a `BaseModel` subclass. If `RootModelRootType` is a `BaseModel` subclass, then the return type will likely be `dict[str, Any]`, as `model_dump` calls are recursive. The return type could even be something different, in the case of a custom serializer. Thus, `Any` is used here to catch all of these cases.

Source code in `pydantic/root_model.py`

```python
def model_dump(  # type: ignore
    self,
    *,
    mode: Literal['json', 'python'] | str = 'python',
    include: Any = None,
    exclude: Any = None,
    context: dict[str, Any] | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal['none', 'warn', 'error'] = True,
    serialize_as_any: bool = False,
) -> Any:
    """This method is included just to get a more accurate return type for type checkers.
    It is included in this `if TYPE_CHECKING:` block since no override is actually necessary.

    See the documentation of `BaseModel.model_dump` for more details about the arguments.

    Generally, this method will have a return type of `RootModelRootType`, assuming that `RootModelRootType` is
    not a `BaseModel` subclass. If `RootModelRootType` is a `BaseModel` subclass, then the return
    type will likely be `dict[str, Any]`, as `model_dump` calls are recursive. The return type could
    even be something different, in the case of a custom serializer.
    Thus, `Any` is used here to catch all of these cases.
    """
    ...

```
