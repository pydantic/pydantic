Bases: `Generic[T]`

Usage Documentation

[`TypeAdapter`](../../concepts/type_adapter/)

Type adapters provide a flexible way to perform validation and serialization based on a Python type.

A `TypeAdapter` instance exposes some of the functionality from `BaseModel` instance methods for types that do not have such methods (such as dataclasses, primitive types, and more).

**Note:** `TypeAdapter` instances are not types, and cannot be used as type annotations for fields.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `type` | `Any` | The type associated with the TypeAdapter. | *required* | | `config` | `ConfigDict | None` | Configuration for the TypeAdapter, should be a dictionary conforming to ConfigDict. Note You cannot provide a configuration when instantiating a TypeAdapter if the type you're using has its own config that cannot be overridden (ex: BaseModel, TypedDict, and dataclass). A type-adapter-config-unused error will be raised in this case. | `None` | | `_parent_depth` | `int` | Depth at which to search for the parent frame. This frame is used when resolving forward annotations during schema building, by looking for the globals and locals of this frame. Defaults to 2, which will result in the frame where the TypeAdapter was instantiated. Note This parameter is named with an underscore to suggest its private nature and discourage use. It may be deprecated in a minor version, so we only recommend using it if you're comfortable with potential change in behavior/support. It's default value is 2 because internally, the TypeAdapter class makes another call to fetch the frame. | `2` | | `module` | `str | None` | The module that passes to plugin if provided. | `None` |

Attributes:

| Name | Type | Description | | --- | --- | --- | | `core_schema` | `CoreSchema` | The core schema for the type. | | `validator` | `SchemaValidator | PluggableSchemaValidator` | The schema validator for the type. | | `serializer` | `SchemaSerializer` | The schema serializer for the type. | | `pydantic_complete` | `bool` | Whether the core schema for the type is successfully built. |

Compatibility with `mypy`

Depending on the type used, `mypy` might raise an error when instantiating a `TypeAdapter`. As a workaround, you can explicitly annotate your variable:

```py
from typing import Union

from pydantic import TypeAdapter

ta: TypeAdapter[Union[str, int]] = TypeAdapter(Union[str, int])  # type: ignore[arg-type]

```

Namespace management nuances and implementation details

Here, we collect some notes on namespace management, and subtle differences from `BaseModel`:

`BaseModel` uses its own `__module__` to find out where it was defined and then looks for symbols to resolve forward references in those globals. On the other hand, `TypeAdapter` can be initialized with arbitrary objects, which may not be types and thus do not have a `__module__` available. So instead we look at the globals in our parent stack frame.

It is expected that the `ns_resolver` passed to this function will have the correct namespace for the type we're adapting. See the source code for `TypeAdapter.__init__` and `TypeAdapter.rebuild` for various ways to construct this namespace.

This works for the case where this function is called in a module that has the target of forward references in its scope, but does not always work for more complex cases.

For example, take the following:

a.py

```python
IntList = list[int]
OuterDict = dict[str, 'IntList']

```

b.py

```python
from a import OuterDict

from pydantic import TypeAdapter

IntList = int  # replaces the symbol the forward reference is looking for
v = TypeAdapter(OuterDict)
v({'x': 1})  # should fail but doesn't

```

If `OuterDict` were a `BaseModel`, this would work because it would resolve the forward reference within the `a.py` namespace. But `TypeAdapter(OuterDict)` can't determine what module `OuterDict` came from.

In other words, the assumption that *all* forward references exist in the module we are being called from is not technically always true. Although most of the time it is and it works fine for recursive models and such, `BaseModel`'s behavior isn't perfect either and *can* break in similar ways, so there is no right or wrong between the two.

But at the very least this behavior is *subtly* different from `BaseModel`'s.

Source code in `pydantic/type_adapter.py`

```python
def __init__(
    self,
    type: Any,
    *,
    config: ConfigDict | None = None,
    _parent_depth: int = 2,
    module: str | None = None,
) -> None:
    if _type_has_config(type) and config is not None:
        raise PydanticUserError(
            'Cannot use `config` when the type is a BaseModel, dataclass or TypedDict.'
            ' These types can have their own config and setting the config via the `config`'
            ' parameter to TypeAdapter will not override it, thus the `config` you passed to'
            ' TypeAdapter becomes meaningless, which is probably not what you want.',
            code='type-adapter-config-unused',
        )

    self._type = type
    self._config = config
    self._parent_depth = _parent_depth
    self.pydantic_complete = False

    parent_frame = self._fetch_parent_frame()
    if isinstance(type, types.FunctionType):
        # Special case functions, which are *not* pushed to the `NsResolver` stack and without this special case
        # would only have access to the parent namespace where the `TypeAdapter` was instantiated (if the function is defined
        # in another module, we need to look at that module's globals).
        if parent_frame is not None:
            # `f_locals` is the namespace where the type adapter was instantiated (~ to `f_globals` if at the module level):
            parent_ns = parent_frame.f_locals
        else:  # pragma: no cover
            parent_ns = None
        globalns, localns = _namespace_utils.ns_for_function(
            type,
            parent_namespace=parent_ns,
        )
        parent_namespace = None
    else:
        if parent_frame is not None:
            globalns = parent_frame.f_globals
            # Do not provide a local ns if the type adapter happens to be instantiated at the module level:
            localns = parent_frame.f_locals if parent_frame.f_locals is not globalns else {}
        else:  # pragma: no cover
            globalns = {}
            localns = {}
        parent_namespace = localns

    self._module_name = module or cast(str, globalns.get('__name__', ''))
    self._init_core_attrs(
        ns_resolver=_namespace_utils.NsResolver(
            namespaces_tuple=_namespace_utils.NamespacesTuple(locals=localns, globals=globalns),
            parent_namespace=parent_namespace,
        ),
        force=False,
    )

```

## rebuild

```python
rebuild(
    *,
    force: bool = False,
    raise_errors: bool = True,
    _parent_namespace_depth: int = 2,
    _types_namespace: MappingNamespace | None = None
) -> bool | None

```

Try to rebuild the pydantic-core schema for the adapter's type.

This may be necessary when one of the annotations is a ForwardRef which could not be resolved during the initial attempt to build the schema, and automatic rebuilding fails.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `force` | `bool` | Whether to force the rebuilding of the type adapter's schema, defaults to False. | `False` | | `raise_errors` | `bool` | Whether to raise errors, defaults to True. | `True` | | `_parent_namespace_depth` | `int` | Depth at which to search for the parent frame. This frame is used when resolving forward annotations during schema rebuilding, by looking for the locals of this frame. Defaults to 2, which will result in the frame where the method was called. | `2` | | `_types_namespace` | `MappingNamespace | None` | An explicit types namespace to use, instead of using the local namespace from the parent frame. Defaults to None. | `None` |

Returns:

| Type | Description | | --- | --- | | `bool | None` | Returns None if the schema is already "complete" and rebuilding was not required. | | `bool | None` | If rebuilding was required, returns True if rebuilding was successful, otherwise False. |

Source code in `pydantic/type_adapter.py`

```python
def rebuild(
    self,
    *,
    force: bool = False,
    raise_errors: bool = True,
    _parent_namespace_depth: int = 2,
    _types_namespace: _namespace_utils.MappingNamespace | None = None,
) -> bool | None:
    """Try to rebuild the pydantic-core schema for the adapter's type.

    This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
    the initial attempt to build the schema, and automatic rebuilding fails.

    Args:
        force: Whether to force the rebuilding of the type adapter's schema, defaults to `False`.
        raise_errors: Whether to raise errors, defaults to `True`.
        _parent_namespace_depth: Depth at which to search for the [parent frame][frame-objects]. This
            frame is used when resolving forward annotations during schema rebuilding, by looking for
            the locals of this frame. Defaults to 2, which will result in the frame where the method
            was called.
        _types_namespace: An explicit types namespace to use, instead of using the local namespace
            from the parent frame. Defaults to `None`.

    Returns:
        Returns `None` if the schema is already "complete" and rebuilding was not required.
        If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.
    """
    if not force and self.pydantic_complete:
        return None

    if _types_namespace is not None:
        rebuild_ns = _types_namespace
    elif _parent_namespace_depth > 0:
        rebuild_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth, force=True) or {}
    else:
        rebuild_ns = {}

    # we have to manually fetch globals here because there's no type on the stack of the NsResolver
    # and so we skip the globalns = get_module_ns_of(typ) call that would normally happen
    globalns = sys._getframe(max(_parent_namespace_depth - 1, 1)).f_globals
    ns_resolver = _namespace_utils.NsResolver(
        namespaces_tuple=_namespace_utils.NamespacesTuple(locals=rebuild_ns, globals=globalns),
        parent_namespace=rebuild_ns,
    )
    return self._init_core_attrs(ns_resolver=ns_resolver, force=True, raise_errors=raise_errors)

```

## validate_python

```python
validate_python(
    object: Any,
    /,
    *,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    from_attributes: bool | None = None,
    context: Any | None = None,
    experimental_allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T

```

Validate a Python object against the model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `object` | `Any` | The Python object to validate against the model. | *required* | | `strict` | `bool | None` | Whether to strictly check types. | `None` | | `extra` | `ExtraValues | None` | Whether to ignore, allow, or forbid extra data during model validation. See the extra configuration value for details. | `None` | | `from_attributes` | `bool | None` | Whether to extract data from object attributes. | `None` | | `context` | `Any | None` | Additional context to pass to the validator. | `None` | | `experimental_allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Experimental whether to enable partial validation, e.g. to process streams. * False / 'off': Default behavior, no partial validation. * True / 'on': Enable partial validation. * 'trailing-strings': Enable partial validation and allow trailing strings in the input. | `False` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Note

When using `TypeAdapter` with a Pydantic `dataclass`, the use of the `from_attributes` argument is not supported.

Returns:

| Type | Description | | --- | --- | | `T` | The validated object. |

Source code in `pydantic/type_adapter.py`

```python
def validate_python(
    self,
    object: Any,
    /,
    *,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    from_attributes: bool | None = None,
    context: Any | None = None,
    experimental_allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T:
    """Validate a Python object against the model.

    Args:
        object: The Python object to validate against the model.
        strict: Whether to strictly check types.
        extra: Whether to ignore, allow, or forbid extra data during model validation.
            See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
        from_attributes: Whether to extract data from object attributes.
        context: Additional context to pass to the validator.
        experimental_allow_partial: **Experimental** whether to enable
            [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
            * False / 'off': Default behavior, no partial validation.
            * True / 'on': Enable partial validation.
            * 'trailing-strings': Enable partial validation and allow trailing strings in the input.
        by_alias: Whether to use the field's alias when validating against the provided input data.
        by_name: Whether to use the field's name when validating against the provided input data.

    !!! note
        When using `TypeAdapter` with a Pydantic `dataclass`, the use of the `from_attributes`
        argument is not supported.

    Returns:
        The validated object.
    """
    if by_alias is False and by_name is not True:
        raise PydanticUserError(
            'At least one of `by_alias` or `by_name` must be set to True.',
            code='validate-by-alias-and-name-false',
        )

    return self.validator.validate_python(
        object,
        strict=strict,
        extra=extra,
        from_attributes=from_attributes,
        context=context,
        allow_partial=experimental_allow_partial,
        by_alias=by_alias,
        by_name=by_name,
    )

```

## validate_json

```python
validate_json(
    data: str | bytes | bytearray,
    /,
    *,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    context: Any | None = None,
    experimental_allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T

```

Usage Documentation

[JSON Parsing](../../concepts/json/#json-parsing)

Validate a JSON string or bytes against the model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `data` | `str | bytes | bytearray` | The JSON data to validate against the model. | *required* | | `strict` | `bool | None` | Whether to strictly check types. | `None` | | `extra` | `ExtraValues | None` | Whether to ignore, allow, or forbid extra data during model validation. See the extra configuration value for details. | `None` | | `context` | `Any | None` | Additional context to use during validation. | `None` | | `experimental_allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Experimental whether to enable partial validation, e.g. to process streams. * False / 'off': Default behavior, no partial validation. * True / 'on': Enable partial validation. * 'trailing-strings': Enable partial validation and allow trailing strings in the input. | `False` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Returns:

| Type | Description | | --- | --- | | `T` | The validated object. |

Source code in `pydantic/type_adapter.py`

```python
def validate_json(
    self,
    data: str | bytes | bytearray,
    /,
    *,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    context: Any | None = None,
    experimental_allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T:
    """!!! abstract "Usage Documentation"
        [JSON Parsing](../concepts/json.md#json-parsing)

    Validate a JSON string or bytes against the model.

    Args:
        data: The JSON data to validate against the model.
        strict: Whether to strictly check types.
        extra: Whether to ignore, allow, or forbid extra data during model validation.
            See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
        context: Additional context to use during validation.
        experimental_allow_partial: **Experimental** whether to enable
            [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
            * False / 'off': Default behavior, no partial validation.
            * True / 'on': Enable partial validation.
            * 'trailing-strings': Enable partial validation and allow trailing strings in the input.
        by_alias: Whether to use the field's alias when validating against the provided input data.
        by_name: Whether to use the field's name when validating against the provided input data.

    Returns:
        The validated object.
    """
    if by_alias is False and by_name is not True:
        raise PydanticUserError(
            'At least one of `by_alias` or `by_name` must be set to True.',
            code='validate-by-alias-and-name-false',
        )

    return self.validator.validate_json(
        data,
        strict=strict,
        extra=extra,
        context=context,
        allow_partial=experimental_allow_partial,
        by_alias=by_alias,
        by_name=by_name,
    )

```

## validate_strings

```python
validate_strings(
    obj: Any,
    /,
    *,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    context: Any | None = None,
    experimental_allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T

```

Validate object contains string data against the model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `obj` | `Any` | The object contains string data to validate. | *required* | | `strict` | `bool | None` | Whether to strictly check types. | `None` | | `extra` | `ExtraValues | None` | Whether to ignore, allow, or forbid extra data during model validation. See the extra configuration value for details. | `None` | | `context` | `Any | None` | Additional context to use during validation. | `None` | | `experimental_allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Experimental whether to enable partial validation, e.g. to process streams. * False / 'off': Default behavior, no partial validation. * True / 'on': Enable partial validation. * 'trailing-strings': Enable partial validation and allow trailing strings in the input. | `False` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Returns:

| Type | Description | | --- | --- | | `T` | The validated object. |

Source code in `pydantic/type_adapter.py`

```python
def validate_strings(
    self,
    obj: Any,
    /,
    *,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    context: Any | None = None,
    experimental_allow_partial: bool | Literal['off', 'on', 'trailing-strings'] = False,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T:
    """Validate object contains string data against the model.

    Args:
        obj: The object contains string data to validate.
        strict: Whether to strictly check types.
        extra: Whether to ignore, allow, or forbid extra data during model validation.
            See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
        context: Additional context to use during validation.
        experimental_allow_partial: **Experimental** whether to enable
            [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
            * False / 'off': Default behavior, no partial validation.
            * True / 'on': Enable partial validation.
            * 'trailing-strings': Enable partial validation and allow trailing strings in the input.
        by_alias: Whether to use the field's alias when validating against the provided input data.
        by_name: Whether to use the field's name when validating against the provided input data.

    Returns:
        The validated object.
    """
    if by_alias is False and by_name is not True:
        raise PydanticUserError(
            'At least one of `by_alias` or `by_name` must be set to True.',
            code='validate-by-alias-and-name-false',
        )

    return self.validator.validate_strings(
        obj,
        strict=strict,
        extra=extra,
        context=context,
        allow_partial=experimental_allow_partial,
        by_alias=by_alias,
        by_name=by_name,
    )

```

## get_default_value

```python
get_default_value(
    *,
    strict: bool | None = None,
    context: Any | None = None
) -> Some[T] | None

```

Get the default value for the wrapped type.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether to strictly check types. | `None` | | `context` | `Any | None` | Additional context to pass to the validator. | `None` |

Returns:

| Type | Description | | --- | --- | | `Some[T] | None` | The default value wrapped in a Some if there is one or None if not. |

Source code in `pydantic/type_adapter.py`

```python
def get_default_value(self, *, strict: bool | None = None, context: Any | None = None) -> Some[T] | None:
    """Get the default value for the wrapped type.

    Args:
        strict: Whether to strictly check types.
        context: Additional context to pass to the validator.

    Returns:
        The default value wrapped in a `Some` if there is one or None if not.
    """
    return self.validator.get_default_value(strict=strict, context=context)

```

## dump_python

```python
dump_python(
    instance: T,
    /,
    *,
    mode: Literal["json", "python"] = "python",
    include: IncEx | None = None,
    exclude: IncEx | None = None,
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
    context: Any | None = None,
) -> Any

```

Dump an instance of the adapted type to a Python object.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `instance` | `T` | The Python object to serialize. | *required* | | `mode` | `Literal['json', 'python']` | The output format. | `'python'` | | `include` | `IncEx | None` | Fields to include in the output. | `None` | | `exclude` | `IncEx | None` | Fields to exclude from the output. | `None` | | `by_alias` | `bool | None` | Whether to use alias names for field names. | `None` | | `exclude_unset` | `bool` | Whether to exclude unset fields. | `False` | | `exclude_defaults` | `bool` | Whether to exclude fields with default values. | `False` | | `exclude_none` | `bool` | Whether to exclude fields with None values. | `False` | | `exclude_computed_fields` | `bool` | Whether to exclude computed fields. While this can be useful for round-tripping, it is usually recommended to use the dedicated round_trip parameter instead. | `False` | | `round_trip` | `bool` | Whether to output the serialized data in a way that is compatible with deserialization. | `False` | | `warnings` | `bool | Literal['none', 'warn', 'error']` | How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors, "error" raises a PydanticSerializationError. | `True` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered. If not provided, a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `context` | `Any | None` | Additional context to pass to the serializer. | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | The serialized object. |

Source code in `pydantic/type_adapter.py`

```python
def dump_python(
    self,
    instance: T,
    /,
    *,
    mode: Literal['json', 'python'] = 'python',
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal['none', 'warn', 'error'] = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    context: Any | None = None,
) -> Any:
    """Dump an instance of the adapted type to a Python object.

    Args:
        instance: The Python object to serialize.
        mode: The output format.
        include: Fields to include in the output.
        exclude: Fields to exclude from the output.
        by_alias: Whether to use alias names for field names.
        exclude_unset: Whether to exclude unset fields.
        exclude_defaults: Whether to exclude fields with default values.
        exclude_none: Whether to exclude fields with None values.
        exclude_computed_fields: Whether to exclude computed fields.
            While this can be useful for round-tripping, it is usually recommended to use the dedicated
            `round_trip` parameter instead.
        round_trip: Whether to output the serialized data in a way that is compatible with deserialization.
        warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
            "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
        fallback: A function to call when an unknown value is encountered. If not provided,
            a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
        serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        context: Additional context to pass to the serializer.

    Returns:
        The serialized object.
    """
    return self.serializer.to_python(
        instance,
        mode=mode,
        by_alias=by_alias,
        include=include,
        exclude=exclude,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        exclude_computed_fields=exclude_computed_fields,
        round_trip=round_trip,
        warnings=warnings,
        fallback=fallback,
        serialize_as_any=serialize_as_any,
        context=context,
    )

```

## dump_json

```python
dump_json(
    instance: T,
    /,
    *,
    indent: int | None = None,
    ensure_ascii: bool = False,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
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
    context: Any | None = None,
) -> bytes

```

Usage Documentation

[JSON Serialization](../../concepts/json/#json-serialization)

Serialize an instance of the adapted type to JSON.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `instance` | `T` | The instance to be serialized. | *required* | | `indent` | `int | None` | Number of spaces for JSON indentation. | `None` | | `ensure_ascii` | `bool` | If True, the output is guaranteed to have all incoming non-ASCII characters escaped. If False (the default), these characters will be output as-is. | `False` | | `include` | `IncEx | None` | Fields to include. | `None` | | `exclude` | `IncEx | None` | Fields to exclude. | `None` | | `by_alias` | `bool | None` | Whether to use alias names for field names. | `None` | | `exclude_unset` | `bool` | Whether to exclude unset fields. | `False` | | `exclude_defaults` | `bool` | Whether to exclude fields with default values. | `False` | | `exclude_none` | `bool` | Whether to exclude fields with a value of None. | `False` | | `exclude_computed_fields` | `bool` | Whether to exclude computed fields. While this can be useful for round-tripping, it is usually recommended to use the dedicated round_trip parameter instead. | `False` | | `round_trip` | `bool` | Whether to serialize and deserialize the instance to ensure round-tripping. | `False` | | `warnings` | `bool | Literal['none', 'warn', 'error']` | How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors, "error" raises a PydanticSerializationError. | `True` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered. If not provided, a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `context` | `Any | None` | Additional context to pass to the serializer. | `None` |

Returns:

| Type | Description | | --- | --- | | `bytes` | The JSON representation of the given instance as bytes. |

Source code in `pydantic/type_adapter.py`

```python
def dump_json(
    self,
    instance: T,
    /,
    *,
    indent: int | None = None,
    ensure_ascii: bool = False,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal['none', 'warn', 'error'] = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    context: Any | None = None,
) -> bytes:
    """!!! abstract "Usage Documentation"
        [JSON Serialization](../concepts/json.md#json-serialization)

    Serialize an instance of the adapted type to JSON.

    Args:
        instance: The instance to be serialized.
        indent: Number of spaces for JSON indentation.
        ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
            If `False` (the default), these characters will be output as-is.
        include: Fields to include.
        exclude: Fields to exclude.
        by_alias: Whether to use alias names for field names.
        exclude_unset: Whether to exclude unset fields.
        exclude_defaults: Whether to exclude fields with default values.
        exclude_none: Whether to exclude fields with a value of `None`.
        exclude_computed_fields: Whether to exclude computed fields.
            While this can be useful for round-tripping, it is usually recommended to use the dedicated
            `round_trip` parameter instead.
        round_trip: Whether to serialize and deserialize the instance to ensure round-tripping.
        warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
            "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
        fallback: A function to call when an unknown value is encountered. If not provided,
            a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
        serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        context: Additional context to pass to the serializer.

    Returns:
        The JSON representation of the given instance as bytes.
    """
    return self.serializer.to_json(
        instance,
        indent=indent,
        ensure_ascii=ensure_ascii,
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        exclude_computed_fields=exclude_computed_fields,
        round_trip=round_trip,
        warnings=warnings,
        fallback=fallback,
        serialize_as_any=serialize_as_any,
        context=context,
    )

```

## json_schema

```python
json_schema(
    *,
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[
        GenerateJsonSchema
    ] = GenerateJsonSchema,
    mode: JsonSchemaMode = "validation"
) -> dict[str, Any]

```

Generate a JSON schema for the adapted type.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `by_alias` | `bool` | Whether to use alias names for field names. | `True` | | `ref_template` | `str` | The format string used for generating $ref strings. | `DEFAULT_REF_TEMPLATE` | | `schema_generator` | `type[GenerateJsonSchema]` | The generator class used for creating the schema. | `GenerateJsonSchema` | | `mode` | `JsonSchemaMode` | The mode to use for schema generation. | `'validation'` |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | The JSON schema for the model as a dictionary. |

Source code in `pydantic/type_adapter.py`

```python
def json_schema(
    self,
    *,
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    mode: JsonSchemaMode = 'validation',
) -> dict[str, Any]:
    """Generate a JSON schema for the adapted type.

    Args:
        by_alias: Whether to use alias names for field names.
        ref_template: The format string used for generating $ref strings.
        schema_generator: The generator class used for creating the schema.
        mode: The mode to use for schema generation.

    Returns:
        The JSON schema for the model as a dictionary.
    """
    schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
    if isinstance(self.core_schema, _mock_val_ser.MockCoreSchema):
        self.core_schema.rebuild()
        assert not isinstance(self.core_schema, _mock_val_ser.MockCoreSchema), 'this is a bug! please report it'
    return schema_generator_instance.generate(self.core_schema, mode=mode)

```

## json_schemas

```python
json_schemas(
    inputs: Iterable[
        tuple[
            JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]
        ]
    ],
    /,
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[
        GenerateJsonSchema
    ] = GenerateJsonSchema,
) -> tuple[
    dict[
        tuple[JsonSchemaKeyT, JsonSchemaMode],
        JsonSchemaValue,
    ],
    JsonSchemaValue,
]

```

Generate a JSON schema including definitions from multiple type adapters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `inputs` | `Iterable[tuple[JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]]]` | Inputs to schema generation. The first two items will form the keys of the (first) output mapping; the type adapters will provide the core schemas that get converted into definitions in the output JSON schema. | *required* | | `by_alias` | `bool` | Whether to use alias names. | `True` | | `title` | `str | None` | The title for the schema. | `None` | | `description` | `str | None` | The description for the schema. | `None` | | `ref_template` | `str` | The format string used for generating $ref strings. | `DEFAULT_REF_TEMPLATE` | | `schema_generator` | `type[GenerateJsonSchema]` | The generator class used for creating the schema. | `GenerateJsonSchema` |

Returns:

| Type | Description | | --- | --- | | `tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]` | A tuple where: The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have JsonRef references to definitions that are defined in the second returned element.) The second element is a JSON schema containing all definitions referenced in the first returned element, along with the optional title and description keys. |

Source code in `pydantic/type_adapter.py`

```python
@staticmethod
def json_schemas(
    inputs: Iterable[tuple[JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]]],
    /,
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
    """Generate a JSON schema including definitions from multiple type adapters.

    Args:
        inputs: Inputs to schema generation. The first two items will form the keys of the (first)
            output mapping; the type adapters will provide the core schemas that get converted into
            definitions in the output JSON schema.
        by_alias: Whether to use alias names.
        title: The title for the schema.
        description: The description for the schema.
        ref_template: The format string used for generating $ref strings.
        schema_generator: The generator class used for creating the schema.

    Returns:
        A tuple where:

            - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                JsonRef references to definitions that are defined in the second returned element.)
            - The second element is a JSON schema containing all definitions referenced in the first returned
                element, along with the optional title and description keys.

    """
    schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

    inputs_ = []
    for key, mode, adapter in inputs:
        # This is the same pattern we follow for model json schemas - we attempt a core schema rebuild if we detect a mock
        if isinstance(adapter.core_schema, _mock_val_ser.MockCoreSchema):
            adapter.core_schema.rebuild()
            assert not isinstance(adapter.core_schema, _mock_val_ser.MockCoreSchema), (
                'this is a bug! please report it'
            )
        inputs_.append((key, mode, adapter.core_schema))

    json_schemas_map, definitions = schema_generator_instance.generate_definitions(inputs_)

    json_schema: dict[str, Any] = {}
    if definitions:
        json_schema['$defs'] = definitions
    if title:
        json_schema['title'] = title
    if description:
        json_schema['description'] = description

    return json_schemas_map, json_schema

```
