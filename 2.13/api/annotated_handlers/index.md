Type annotations to use with `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__`.

## GetJsonSchemaHandler

Handler to call into the next JSON schema generation function.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `mode` | `JsonSchemaMode` | Json schema mode, can be validation or serialization. |

### resolve_ref_schema

```python
resolve_ref_schema(
    maybe_ref_json_schema: JsonSchemaValue,
) -> JsonSchemaValue

```

Get the real schema for a `{"$ref": ...}` schema. If the schema given is not a `$ref` schema, it will be returned as is. This means you don't have to check before calling this function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `maybe_ref_json_schema` | `JsonSchemaValue` | A JsonSchemaValue which may be a $ref schema. | *required* |

Raises:

| Type | Description | | --- | --- | | `LookupError` | If the ref is not found. |

Returns:

| Name | Type | Description | | --- | --- | --- | | `JsonSchemaValue` | `JsonSchemaValue` | A JsonSchemaValue that has no $ref. |

Source code in `pydantic/annotated_handlers.py`

```python
def resolve_ref_schema(self, maybe_ref_json_schema: JsonSchemaValue, /) -> JsonSchemaValue:
    """Get the real schema for a `{"$ref": ...}` schema.
    If the schema given is not a `$ref` schema, it will be returned as is.
    This means you don't have to check before calling this function.

    Args:
        maybe_ref_json_schema: A JsonSchemaValue which may be a `$ref` schema.

    Raises:
        LookupError: If the ref is not found.

    Returns:
        JsonSchemaValue: A JsonSchemaValue that has no `$ref`.
    """
    raise NotImplementedError

```

## GetCoreSchemaHandler

Handler to call into the next CoreSchema schema generation function.

### field_name

```python
field_name: str | None

```

Get the name of the closest field to this validator.

### generate_schema

```python
generate_schema(source_type: Any) -> CoreSchema

```

Generate a schema unrelated to the current context. Use this function if e.g. you are handling schema generation for a sequence and want to generate a schema for its items. Otherwise, you may end up doing something like applying a `min_length` constraint that was intended for the sequence itself to its items!

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `source_type` | `Any` | The input type. | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `CoreSchema` | `CoreSchema` | The pydantic-core CoreSchema generated. |

Source code in `pydantic/annotated_handlers.py`

```python
def generate_schema(self, source_type: Any, /) -> core_schema.CoreSchema:
    """Generate a schema unrelated to the current context.
    Use this function if e.g. you are handling schema generation for a sequence
    and want to generate a schema for its items.
    Otherwise, you may end up doing something like applying a `min_length` constraint
    that was intended for the sequence itself to its items!

    Args:
        source_type: The input type.

    Returns:
        CoreSchema: The `pydantic-core` CoreSchema generated.
    """
    raise NotImplementedError

```

### resolve_ref_schema

```python
resolve_ref_schema(
    maybe_ref_schema: CoreSchema,
) -> CoreSchema

```

Get the real schema for a `definition-ref` schema. If the schema given is not a `definition-ref` schema, it will be returned as is. This means you don't have to check before calling this function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `maybe_ref_schema` | `CoreSchema` | A CoreSchema, ref-based or not. | *required* |

Raises:

| Type | Description | | --- | --- | | `LookupError` | If the ref is not found. |

Returns:

| Type | Description | | --- | --- | | `CoreSchema` | A concrete CoreSchema. |

Source code in `pydantic/annotated_handlers.py`

```python
def resolve_ref_schema(self, maybe_ref_schema: core_schema.CoreSchema, /) -> core_schema.CoreSchema:
    """Get the real schema for a `definition-ref` schema.
    If the schema given is not a `definition-ref` schema, it will be returned as is.
    This means you don't have to check before calling this function.

    Args:
        maybe_ref_schema: A `CoreSchema`, `ref`-based or not.

    Raises:
        LookupError: If the `ref` is not found.

    Returns:
        A concrete `CoreSchema`.
    """
    raise NotImplementedError

```
