Decorator for validating function calls.

## validate_call

```python
validate_call(
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False
) -> Callable[[AnyCallableT], AnyCallableT]

```

```python
validate_call(func: AnyCallableT) -> AnyCallableT

```

```python
validate_call(
    func: AnyCallableT | None = None,
    /,
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False,
) -> AnyCallableT | Callable[[AnyCallableT], AnyCallableT]

```

Usage Documentation

[Validation Decorator](../../concepts/validation_decorator/)

Returns a decorated wrapper around the function that validates the arguments and, optionally, the return value.

Usage may be either as a plain decorator `@validate_call` or with arguments `@validate_call(...)`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `AnyCallableT | None` | The function to be decorated. | `None` | | `config` | `ConfigDict | None` | The configuration dictionary. | `None` | | `validate_return` | `bool` | Whether to validate the return value. | `False` |

Returns:

| Type | Description | | --- | --- | | `AnyCallableT | Callable[[AnyCallableT], AnyCallableT]` | The decorated function. |

Source code in `pydantic/validate_call_decorator.py`

```python
def validate_call(
    func: AnyCallableT | None = None,
    /,
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False,
) -> AnyCallableT | Callable[[AnyCallableT], AnyCallableT]:
    """!!! abstract "Usage Documentation"
        [Validation Decorator](../concepts/validation_decorator.md)

    Returns a decorated wrapper around the function that validates the arguments and, optionally, the return value.

    Usage may be either as a plain decorator `@validate_call` or with arguments `@validate_call(...)`.

    Args:
        func: The function to be decorated.
        config: The configuration dictionary.
        validate_return: Whether to validate the return value.

    Returns:
        The decorated function.
    """
    parent_namespace = _typing_extra.parent_frame_namespace()

    def validate(function: AnyCallableT) -> AnyCallableT:
        _check_function_type(function)
        validate_call_wrapper = _validate_call.ValidateCallWrapper(
            cast(_generate_schema.ValidateCallSupportedTypes, function), config, validate_return, parent_namespace
        )
        return _validate_call.update_wrapper_attributes(function, validate_call_wrapper.__call__)  # type: ignore

    if func is not None:
        return validate(func)
    else:
        return validate

```
