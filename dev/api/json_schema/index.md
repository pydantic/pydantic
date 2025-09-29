Usage Documentation

[JSON Schema](../../concepts/json_schema/)

The `json_schema` module contains classes and functions to allow the way [JSON Schema](https://json-schema.org/) is generated to be customized.

In general you shouldn't need to use this module directly; instead, you can use BaseModel.model_json_schema and TypeAdapter.json_schema.

## CoreSchemaOrFieldType

```python
CoreSchemaOrFieldType = Literal[
    CoreSchemaType, CoreSchemaFieldType
]

```

A type alias for defined schema types that represents a union of `core_schema.CoreSchemaType` and `core_schema.CoreSchemaFieldType`.

## JsonSchemaValue

```python
JsonSchemaValue = dict[str, Any]

```

A type alias for a JSON schema value. This is a dictionary of string keys to arbitrary JSON values.

## JsonSchemaMode

```python
JsonSchemaMode = Literal['validation', 'serialization']

```

A type alias that represents the mode of a JSON schema; either 'validation' or 'serialization'.

For some types, the inputs to validation differ from the outputs of serialization. For example, computed fields will only be present when serializing, and should not be provided when validating. This flag provides a way to indicate whether you want the JSON schema required for validation inputs, or that will be matched by serialization outputs.

## JsonSchemaWarningKind

```python
JsonSchemaWarningKind = Literal[
    "skipped-choice",
    "non-serializable-default",
    "skipped-discriminator",
]

```

A type alias representing the kinds of warnings that can be emitted during JSON schema generation.

See GenerateJsonSchema.render_warning_message for more details.

## NoDefault

```python
NoDefault = object()

```

A sentinel value used to indicate that no default value should be used when generating a JSON Schema for a core schema with a default value.

## DEFAULT_REF_TEMPLATE

```python
DEFAULT_REF_TEMPLATE = '#/$defs/{model}'

```

The default format string used to generate reference names.

## PydanticJsonSchemaWarning

Bases: `UserWarning`

This class is used to emit warnings produced during JSON schema generation. See the GenerateJsonSchema.emit_warning and GenerateJsonSchema.render_warning_message methods for more details; these can be overridden to control warning behavior.

## GenerateJsonSchema

```python
GenerateJsonSchema(
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
)

```

Usage Documentation

[Customizing the JSON Schema Generation Process](../../concepts/json_schema/#customizing-the-json-schema-generation-process)

A class for generating JSON schemas.

This class generates JSON schemas based on configured parameters. The default schema dialect is <https://json-schema.org/draft/2020-12/schema>. The class uses `by_alias` to configure how fields with multiple names are handled and `ref_template` to format reference names.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `schema_dialect` | | The JSON schema dialect used to generate the schema. See Declaring a Dialect in the JSON Schema documentation for more information about dialects. | | `ignored_warning_kinds` | `set[JsonSchemaWarningKind]` | Warnings to ignore when generating the schema. self.render_warning_message will do nothing if its argument kind is in ignored_warning_kinds; this value can be modified on subclasses to easily control which warnings are emitted. | | `by_alias` | | Whether to use field aliases when generating the schema. | | `ref_template` | | The format string used when generating reference names. | | `core_to_json_refs` | `dict[CoreModeRef, JsonRef]` | A mapping of core refs to JSON refs. | | `core_to_defs_refs` | `dict[CoreModeRef, DefsRef]` | A mapping of core refs to definition refs. | | `defs_to_core_refs` | `dict[DefsRef, CoreModeRef]` | A mapping of definition refs to core refs. | | `json_to_defs_refs` | `dict[JsonRef, DefsRef]` | A mapping of JSON refs to definition refs. | | `definitions` | `dict[DefsRef, JsonSchemaValue]` | Definitions in the schema. |

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `by_alias` | `bool` | Whether to use field aliases in the generated schemas. | `True` | | `ref_template` | `str` | The format string to use when generating reference names. | `DEFAULT_REF_TEMPLATE` |

Raises:

| Type | Description | | --- | --- | | `JsonSchemaError` | If the instance of the class is inadvertently reused after generating a schema. |

Source code in `pydantic/json_schema.py`

```python
def __init__(self, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE):
    self.by_alias = by_alias
    self.ref_template = ref_template

    self.core_to_json_refs: dict[CoreModeRef, JsonRef] = {}
    self.core_to_defs_refs: dict[CoreModeRef, DefsRef] = {}
    self.defs_to_core_refs: dict[DefsRef, CoreModeRef] = {}
    self.json_to_defs_refs: dict[JsonRef, DefsRef] = {}

    self.definitions: dict[DefsRef, JsonSchemaValue] = {}
    self._config_wrapper_stack = _config.ConfigWrapperStack(_config.ConfigWrapper({}))

    self._mode: JsonSchemaMode = 'validation'

    # The following includes a mapping of a fully-unique defs ref choice to a list of preferred
    # alternatives, which are generally simpler, such as only including the class name.
    # At the end of schema generation, we use these to produce a JSON schema with more human-readable
    # definitions, which would also work better in a generated OpenAPI client, etc.
    self._prioritized_defsref_choices: dict[DefsRef, list[DefsRef]] = {}
    self._collision_counter: dict[str, int] = defaultdict(int)
    self._collision_index: dict[str, int] = {}

    self._schema_type_to_method = self.build_schema_type_to_method()

    # When we encounter definitions we need to try to build them immediately
    # so that they are available schemas that reference them
    # But it's possible that CoreSchema was never going to be used
    # (e.g. because the CoreSchema that references short circuits is JSON schema generation without needing
    #  the reference) so instead of failing altogether if we can't build a definition we
    # store the error raised and re-throw it if we end up needing that def
    self._core_defs_invalid_for_json_schema: dict[DefsRef, PydanticInvalidForJsonSchema] = {}

    # This changes to True after generating a schema, to prevent issues caused by accidental reuse
    # of a single instance of a schema generator
    self._used = False

```

### ValidationsMapping

This class just contains mappings from core_schema attribute names to the corresponding JSON schema attribute names. While I suspect it is unlikely to be necessary, you can in principle override this class in a subclass of GenerateJsonSchema (by inheriting from GenerateJsonSchema.ValidationsMapping) to change these mappings.

### build_schema_type_to_method

```python
build_schema_type_to_method() -> dict[
    CoreSchemaOrFieldType,
    Callable[[CoreSchemaOrField], JsonSchemaValue],
]

```

Builds a dictionary mapping fields to methods for generating JSON schemas.

Returns:

| Type | Description | | --- | --- | | `dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]]` | A dictionary containing the mapping of CoreSchemaOrFieldType to a handler method. |

Raises:

| Type | Description | | --- | --- | | `TypeError` | If no method has been defined for generating a JSON schema for a given pydantic core schema type. |

Source code in `pydantic/json_schema.py`

```python
def build_schema_type_to_method(
    self,
) -> dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]]:
    """Builds a dictionary mapping fields to methods for generating JSON schemas.

    Returns:
        A dictionary containing the mapping of `CoreSchemaOrFieldType` to a handler method.

    Raises:
        TypeError: If no method has been defined for generating a JSON schema for a given pydantic core schema type.
    """
    mapping: dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]] = {}
    core_schema_types: list[CoreSchemaOrFieldType] = list(get_literal_values(CoreSchemaOrFieldType))
    for key in core_schema_types:
        method_name = f'{key.replace("-", "_")}_schema'
        try:
            mapping[key] = getattr(self, method_name)
        except AttributeError as e:  # pragma: no cover
            if os.getenv('PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES'):
                continue
            raise TypeError(
                f'No method for generating JsonSchema for core_schema.type={key!r} '
                f'(expected: {type(self).__name__}.{method_name})'
            ) from e
    return mapping

```

### generate_definitions

```python
generate_definitions(
    inputs: Sequence[
        tuple[JsonSchemaKeyT, JsonSchemaMode, CoreSchema]
    ]
) -> tuple[
    dict[
        tuple[JsonSchemaKeyT, JsonSchemaMode],
        JsonSchemaValue,
    ],
    dict[DefsRef, JsonSchemaValue],
]

```

Generates JSON schema definitions from a list of core schemas, pairing the generated definitions with a mapping that links the input keys to the definition references.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `inputs` | `Sequence[tuple[JsonSchemaKeyT, JsonSchemaMode, CoreSchema]]` | A sequence of tuples, where: The first element is a JSON schema key type. The second element is the JSON mode: either 'validation' or 'serialization'. The third element is a core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], dict[DefsRef, JsonSchemaValue]]` | A tuple where: The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have JsonRef references to definitions that are defined in the second returned element.) The second element is a dictionary whose keys are definition references for the JSON schemas from the first returned element, and whose values are the actual JSON schema definitions. |

Raises:

| Type | Description | | --- | --- | | `PydanticUserError` | Raised if the JSON schema generator has already been used to generate a JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def generate_definitions(
    self, inputs: Sequence[tuple[JsonSchemaKeyT, JsonSchemaMode, core_schema.CoreSchema]]
) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], dict[DefsRef, JsonSchemaValue]]:
    """Generates JSON schema definitions from a list of core schemas, pairing the generated definitions with a
    mapping that links the input keys to the definition references.

    Args:
        inputs: A sequence of tuples, where:

            - The first element is a JSON schema key type.
            - The second element is the JSON mode: either 'validation' or 'serialization'.
            - The third element is a core schema.

    Returns:
        A tuple where:

            - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                JsonRef references to definitions that are defined in the second returned element.)
            - The second element is a dictionary whose keys are definition references for the JSON schemas
                from the first returned element, and whose values are the actual JSON schema definitions.

    Raises:
        PydanticUserError: Raised if the JSON schema generator has already been used to generate a JSON schema.
    """
    if self._used:
        raise PydanticUserError(
            'This JSON schema generator has already been used to generate a JSON schema. '
            f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.',
            code='json-schema-already-used',
        )

    for _, mode, schema in inputs:
        self._mode = mode
        self.generate_inner(schema)

    definitions_remapping = self._build_definitions_remapping()

    json_schemas_map: dict[tuple[JsonSchemaKeyT, JsonSchemaMode], DefsRef] = {}
    for key, mode, schema in inputs:
        self._mode = mode
        json_schema = self.generate_inner(schema)
        json_schemas_map[(key, mode)] = definitions_remapping.remap_json_schema(json_schema)

    json_schema = {'$defs': self.definitions}
    json_schema = definitions_remapping.remap_json_schema(json_schema)
    self._used = True
    return json_schemas_map, self.sort(json_schema['$defs'])  # type: ignore

```

### generate

```python
generate(
    schema: CoreSchema, mode: JsonSchemaMode = "validation"
) -> JsonSchemaValue

```

Generates a JSON schema for a specified schema in a specified mode.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | A Pydantic model. | *required* | | `mode` | `JsonSchemaMode` | The mode in which to generate the schema. Defaults to 'validation'. | `'validation'` |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | A JSON schema representing the specified schema. |

Raises:

| Type | Description | | --- | --- | | `PydanticUserError` | If the JSON schema generator has already been used to generate a JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def generate(self, schema: CoreSchema, mode: JsonSchemaMode = 'validation') -> JsonSchemaValue:
    """Generates a JSON schema for a specified schema in a specified mode.

    Args:
        schema: A Pydantic model.
        mode: The mode in which to generate the schema. Defaults to 'validation'.

    Returns:
        A JSON schema representing the specified schema.

    Raises:
        PydanticUserError: If the JSON schema generator has already been used to generate a JSON schema.
    """
    self._mode = mode
    if self._used:
        raise PydanticUserError(
            'This JSON schema generator has already been used to generate a JSON schema. '
            f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.',
            code='json-schema-already-used',
        )

    json_schema: JsonSchemaValue = self.generate_inner(schema)
    json_ref_counts = self.get_json_ref_counts(json_schema)

    ref = cast(JsonRef, json_schema.get('$ref'))
    while ref is not None:  # may need to unpack multiple levels
        ref_json_schema = self.get_schema_from_definitions(ref)
        if json_ref_counts[ref] == 1 and ref_json_schema is not None and len(json_schema) == 1:
            # "Unpack" the ref since this is the only reference and there are no sibling keys
            json_schema = ref_json_schema.copy()  # copy to prevent recursive dict reference
            json_ref_counts[ref] -= 1
            ref = cast(JsonRef, json_schema.get('$ref'))
        ref = None

    self._garbage_collect_definitions(json_schema)
    definitions_remapping = self._build_definitions_remapping()

    if self.definitions:
        json_schema['$defs'] = self.definitions

    json_schema = definitions_remapping.remap_json_schema(json_schema)

    # For now, we will not set the $schema key. However, if desired, this can be easily added by overriding
    # this method and adding the following line after a call to super().generate(schema):
    # json_schema['$schema'] = self.schema_dialect

    self._used = True
    return self.sort(json_schema)

```

### generate_inner

```python
generate_inner(
    schema: CoreSchemaOrField,
) -> JsonSchemaValue

```

Generates a JSON schema for a given core schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchemaOrField` | The given core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

TODO: the nested function definitions here seem like bad practice, I'd like to unpack these in a future PR. It'd be great if we could shorten the call stack a bit for JSON schema generation, and I think there's potential for that here.

Source code in `pydantic/json_schema.py`

```python
def generate_inner(self, schema: CoreSchemaOrField) -> JsonSchemaValue:  # noqa: C901
    """Generates a JSON schema for a given core schema.

    Args:
        schema: The given core schema.

    Returns:
        The generated JSON schema.

    TODO: the nested function definitions here seem like bad practice, I'd like to unpack these
    in a future PR. It'd be great if we could shorten the call stack a bit for JSON schema generation,
    and I think there's potential for that here.
    """
    # If a schema with the same CoreRef has been handled, just return a reference to it
    # Note that this assumes that it will _never_ be the case that the same CoreRef is used
    # on types that should have different JSON schemas
    if 'ref' in schema:
        core_ref = CoreRef(schema['ref'])  # type: ignore[typeddict-item]
        core_mode_ref = (core_ref, self.mode)
        if core_mode_ref in self.core_to_defs_refs and self.core_to_defs_refs[core_mode_ref] in self.definitions:
            return {'$ref': self.core_to_json_refs[core_mode_ref]}

    def populate_defs(core_schema: CoreSchema, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        if 'ref' in core_schema:
            core_ref = CoreRef(core_schema['ref'])  # type: ignore[typeddict-item]
            defs_ref, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
            json_ref = JsonRef(ref_json_schema['$ref'])
            # Replace the schema if it's not a reference to itself
            # What we want to avoid is having the def be just a ref to itself
            # which is what would happen if we blindly assigned any
            if json_schema.get('$ref', None) != json_ref:
                self.definitions[defs_ref] = json_schema
                self._core_defs_invalid_for_json_schema.pop(defs_ref, None)
            json_schema = ref_json_schema
        return json_schema

    def handler_func(schema_or_field: CoreSchemaOrField) -> JsonSchemaValue:
        """Generate a JSON schema based on the input schema.

        Args:
            schema_or_field: The core schema to generate a JSON schema from.

        Returns:
            The generated JSON schema.

        Raises:
            TypeError: If an unexpected schema type is encountered.
        """
        # Generate the core-schema-type-specific bits of the schema generation:
        json_schema: JsonSchemaValue | None = None
        if self.mode == 'serialization' and 'serialization' in schema_or_field:
            # In this case, we skip the JSON Schema generation of the schema
            # and use the `'serialization'` schema instead (canonical example:
            # `Annotated[int, PlainSerializer(str)]`).
            ser_schema = schema_or_field['serialization']  # type: ignore
            json_schema = self.ser_schema(ser_schema)

            # It might be that the 'serialization'` is skipped depending on `when_used`.
            # This is only relevant for `nullable` schemas though, so we special case here.
            if (
                json_schema is not None
                and ser_schema.get('when_used') in ('unless-none', 'json-unless-none')
                and schema_or_field['type'] == 'nullable'
            ):
                json_schema = self.get_flattened_anyof([{'type': 'null'}, json_schema])
        if json_schema is None:
            if _core_utils.is_core_schema(schema_or_field) or _core_utils.is_core_schema_field(schema_or_field):
                generate_for_schema_type = self._schema_type_to_method[schema_or_field['type']]
                json_schema = generate_for_schema_type(schema_or_field)
            else:
                raise TypeError(f'Unexpected schema type: schema={schema_or_field}')

        return json_schema

    current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, handler_func)

    metadata = cast(_core_metadata.CoreMetadata, schema.get('metadata', {}))

    # TODO: I dislike that we have to wrap these basic dict updates in callables, is there any way around this?

    if js_updates := metadata.get('pydantic_js_updates'):

        def js_updates_handler_func(
            schema_or_field: CoreSchemaOrField,
            current_handler: GetJsonSchemaHandler = current_handler,
        ) -> JsonSchemaValue:
            json_schema = {**current_handler(schema_or_field), **js_updates}
            return json_schema

        current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, js_updates_handler_func)

    if js_extra := metadata.get('pydantic_js_extra'):

        def js_extra_handler_func(
            schema_or_field: CoreSchemaOrField,
            current_handler: GetJsonSchemaHandler = current_handler,
        ) -> JsonSchemaValue:
            json_schema = current_handler(schema_or_field)
            if isinstance(js_extra, dict):
                json_schema.update(to_jsonable_python(js_extra))
            elif callable(js_extra):
                # similar to typing issue in _update_class_schema when we're working with callable js extra
                js_extra(json_schema)  # type: ignore
            return json_schema

        current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, js_extra_handler_func)

    for js_modify_function in metadata.get('pydantic_js_functions', ()):

        def new_handler_func(
            schema_or_field: CoreSchemaOrField,
            current_handler: GetJsonSchemaHandler = current_handler,
            js_modify_function: GetJsonSchemaFunction = js_modify_function,
        ) -> JsonSchemaValue:
            json_schema = js_modify_function(schema_or_field, current_handler)
            if _core_utils.is_core_schema(schema_or_field):
                json_schema = populate_defs(schema_or_field, json_schema)
            original_schema = current_handler.resolve_ref_schema(json_schema)
            ref = json_schema.pop('$ref', None)
            if ref and json_schema:
                original_schema.update(json_schema)
            return original_schema

        current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, new_handler_func)

    for js_modify_function in metadata.get('pydantic_js_annotation_functions', ()):

        def new_handler_func(
            schema_or_field: CoreSchemaOrField,
            current_handler: GetJsonSchemaHandler = current_handler,
            js_modify_function: GetJsonSchemaFunction = js_modify_function,
        ) -> JsonSchemaValue:
            return js_modify_function(schema_or_field, current_handler)

        current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, new_handler_func)

    json_schema = current_handler(schema)
    if _core_utils.is_core_schema(schema):
        json_schema = populate_defs(schema, json_schema)
    return json_schema

```

### sort

```python
sort(
    value: JsonSchemaValue, parent_key: str | None = None
) -> JsonSchemaValue

```

Override this method to customize the sorting of the JSON schema (e.g., don't sort at all, sort all keys unconditionally, etc.)

By default, alphabetically sort the keys in the JSON schema, skipping the 'properties' and 'default' keys to preserve field definition order. This sort is recursive, so it will sort all nested dictionaries as well.

Source code in `pydantic/json_schema.py`

```python
def sort(self, value: JsonSchemaValue, parent_key: str | None = None) -> JsonSchemaValue:
    """Override this method to customize the sorting of the JSON schema (e.g., don't sort at all, sort all keys unconditionally, etc.)

    By default, alphabetically sort the keys in the JSON schema, skipping the 'properties' and 'default' keys to preserve field definition order.
    This sort is recursive, so it will sort all nested dictionaries as well.
    """
    sorted_dict: dict[str, JsonSchemaValue] = {}
    keys = value.keys()
    if parent_key not in ('properties', 'default'):
        keys = sorted(keys)
    for key in keys:
        sorted_dict[key] = self._sort_recursive(value[key], parent_key=key)
    return sorted_dict

```

### invalid_schema

```python
invalid_schema(schema: InvalidSchema) -> JsonSchemaValue

```

Placeholder - should never be called.

Source code in `pydantic/json_schema.py`

```python
def invalid_schema(self, schema: core_schema.InvalidSchema) -> JsonSchemaValue:
    """Placeholder - should never be called."""

    raise RuntimeError('Cannot generate schema for invalid_schema. This is a bug! Please report it.')

```

### any_schema

```python
any_schema(schema: AnySchema) -> JsonSchemaValue

```

Generates a JSON schema that matches any value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `AnySchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def any_schema(self, schema: core_schema.AnySchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches any value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {}

```

### none_schema

```python
none_schema(schema: NoneSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches `None`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `NoneSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def none_schema(self, schema: core_schema.NoneSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches `None`.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'null'}

```

### bool_schema

```python
bool_schema(schema: BoolSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a bool value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `BoolSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def bool_schema(self, schema: core_schema.BoolSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a bool value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'boolean'}

```

### int_schema

```python
int_schema(schema: IntSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches an int value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `IntSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def int_schema(self, schema: core_schema.IntSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches an int value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema: dict[str, Any] = {'type': 'integer'}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
    json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
    return json_schema

```

### float_schema

```python
float_schema(schema: FloatSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a float value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `FloatSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def float_schema(self, schema: core_schema.FloatSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a float value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema: dict[str, Any] = {'type': 'number'}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
    json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
    return json_schema

```

### decimal_schema

```python
decimal_schema(schema: DecimalSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a decimal value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DecimalSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def decimal_schema(self, schema: core_schema.DecimalSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a decimal value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """

    def get_decimal_pattern(schema: core_schema.DecimalSchema) -> str:
        max_digits = schema.get('max_digits')
        decimal_places = schema.get('decimal_places')

        pattern = (
            r'^(?!^[-+.]*$)[+-]?0*'  # check it is not empty string and not one or sequence of ".+-" characters.
        )

        # Case 1: Both max_digits and decimal_places are set
        if max_digits is not None and decimal_places is not None:
            integer_places = max(0, max_digits - decimal_places)
            pattern += (
                rf'(?:'
                rf'\d{{0,{integer_places}}}'
                rf'|'
                rf'(?=[\d.]{{1,{max_digits + 1}}}0*$)'
                rf'\d{{0,{integer_places}}}\.\d{{0,{decimal_places}}}0*$'
                rf')'
            )

        # Case 2: Only max_digits is set
        elif max_digits is not None and decimal_places is None:
            pattern += (
                rf'(?:'
                rf'\d{{0,{max_digits}}}'
                rf'|'
                rf'(?=[\d.]{{1,{max_digits + 1}}}0*$)'
                rf'\d*\.\d*0*$'
                rf')'
            )

        # Case 3: Only decimal_places is set
        elif max_digits is None and decimal_places is not None:
            pattern += rf'\d*\.?\d{{0,{decimal_places}}}0*$'

        # Case 4: Both are None (no restrictions)
        else:
            pattern += r'\d*\.?\d*$'  # look for arbitrary integer or decimal

        return pattern

    json_schema = self.str_schema(core_schema.str_schema(pattern=get_decimal_pattern(schema)))
    if self.mode == 'validation':
        multiple_of = schema.get('multiple_of')
        le = schema.get('le')
        ge = schema.get('ge')
        lt = schema.get('lt')
        gt = schema.get('gt')
        json_schema = {
            'anyOf': [
                self.float_schema(
                    core_schema.float_schema(
                        allow_inf_nan=schema.get('allow_inf_nan'),
                        multiple_of=None if multiple_of is None else float(multiple_of),
                        le=None if le is None else float(le),
                        ge=None if ge is None else float(ge),
                        lt=None if lt is None else float(lt),
                        gt=None if gt is None else float(gt),
                    )
                ),
                json_schema,
            ],
        }
    return json_schema

```

### str_schema

```python
str_schema(schema: StringSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a string value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `StringSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def str_schema(self, schema: core_schema.StringSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a string value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema = {'type': 'string'}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
    if isinstance(json_schema.get('pattern'), Pattern):
        # TODO: should we add regex flags to the pattern?
        json_schema['pattern'] = json_schema.get('pattern').pattern  # type: ignore
    return json_schema

```

### bytes_schema

```python
bytes_schema(schema: BytesSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a bytes value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `BytesSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def bytes_schema(self, schema: core_schema.BytesSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a bytes value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema = {'type': 'string', 'format': 'base64url' if self._config.ser_json_bytes == 'base64' else 'binary'}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.bytes)
    return json_schema

```

### date_schema

```python
date_schema(schema: DateSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a date value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DateSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a date value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'string', 'format': 'date'}

```

### time_schema

```python
time_schema(schema: TimeSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a time value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `TimeSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a time value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'string', 'format': 'time'}

```

### datetime_schema

```python
datetime_schema(schema: DatetimeSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a datetime value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DatetimeSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a datetime value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'string', 'format': 'date-time'}

```

### timedelta_schema

```python
timedelta_schema(
    schema: TimedeltaSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a timedelta value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `TimedeltaSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a timedelta value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    if self._config.ser_json_timedelta == 'float':
        return {'type': 'number'}
    return {'type': 'string', 'format': 'duration'}

```

### literal_schema

```python
literal_schema(schema: LiteralSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a literal value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `LiteralSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a literal value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    expected = [to_jsonable_python(v.value if isinstance(v, Enum) else v) for v in schema['expected']]

    result: dict[str, Any] = {}
    if len(expected) == 1:
        result['const'] = expected[0]
    else:
        result['enum'] = expected

    types = {type(e) for e in expected}
    if types == {str}:
        result['type'] = 'string'
    elif types == {int}:
        result['type'] = 'integer'
    elif types == {float}:
        result['type'] = 'number'
    elif types == {bool}:
        result['type'] = 'boolean'
    elif types == {list}:
        result['type'] = 'array'
    elif types == {type(None)}:
        result['type'] = 'null'
    return result

```

### missing_sentinel_schema

```python
missing_sentinel_schema(
    schema: MissingSentinelSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches the `MISSING` sentinel value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `MissingSentinelSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def missing_sentinel_schema(self, schema: core_schema.MissingSentinelSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches the `MISSING` sentinel value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    raise PydanticOmit

```

### enum_schema

```python
enum_schema(schema: EnumSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches an Enum value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `EnumSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches an Enum value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    enum_type = schema['cls']
    description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
    if (
        description == 'An enumeration.'
    ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
        description = None
    result: dict[str, Any] = {'title': enum_type.__name__, 'description': description}
    result = {k: v for k, v in result.items() if v is not None}

    expected = [to_jsonable_python(v.value) for v in schema['members']]

    result['enum'] = expected

    types = {type(e) for e in expected}
    if isinstance(enum_type, str) or types == {str}:
        result['type'] = 'string'
    elif isinstance(enum_type, int) or types == {int}:
        result['type'] = 'integer'
    elif isinstance(enum_type, float) or types == {float}:
        result['type'] = 'number'
    elif types == {bool}:
        result['type'] = 'boolean'
    elif types == {list}:
        result['type'] = 'array'

    return result

```

### is_instance_schema

```python
is_instance_schema(
    schema: IsInstanceSchema,
) -> JsonSchemaValue

```

Handles JSON schema generation for a core schema that checks if a value is an instance of a class.

Unless overridden in a subclass, this raises an error.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `IsInstanceSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
    """Handles JSON schema generation for a core schema that checks if a value is an instance of a class.

    Unless overridden in a subclass, this raises an error.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.handle_invalid_for_json_schema(schema, f'core_schema.IsInstanceSchema ({schema["cls"]})')

```

### is_subclass_schema

```python
is_subclass_schema(
    schema: IsSubclassSchema,
) -> JsonSchemaValue

```

Handles JSON schema generation for a core schema that checks if a value is a subclass of a class.

For backwards compatibility with v1, this does not raise an error, but can be overridden to change this.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `IsSubclassSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
    """Handles JSON schema generation for a core schema that checks if a value is a subclass of a class.

    For backwards compatibility with v1, this does not raise an error, but can be overridden to change this.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    # Note: This is for compatibility with V1; you can override if you want different behavior.
    return {}

```

### callable_schema

```python
callable_schema(schema: CallableSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a callable value.

Unless overridden in a subclass, this raises an error.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CallableSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a callable value.

    Unless overridden in a subclass, this raises an error.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.handle_invalid_for_json_schema(schema, 'core_schema.CallableSchema')

```

### list_schema

```python
list_schema(schema: ListSchema) -> JsonSchemaValue

```

Returns a schema that matches a list schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ListSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
    """Returns a schema that matches a list schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
    json_schema = {'type': 'array', 'items': items_schema}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
    return json_schema

```

### tuple_positional_schema

```python
tuple_positional_schema(
    schema: TupleSchema,
) -> JsonSchemaValue

```

Replaced by `tuple_schema`.

Source code in `pydantic/json_schema.py`

```python
@deprecated('`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.', category=None)
@final
def tuple_positional_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
    """Replaced by `tuple_schema`."""
    warnings.warn(
        '`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.',
        PydanticDeprecatedSince26,
        stacklevel=2,
    )
    return self.tuple_schema(schema)

```

### tuple_variable_schema

```python
tuple_variable_schema(
    schema: TupleSchema,
) -> JsonSchemaValue

```

Replaced by `tuple_schema`.

Source code in `pydantic/json_schema.py`

```python
@deprecated('`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.', category=None)
@final
def tuple_variable_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
    """Replaced by `tuple_schema`."""
    warnings.warn(
        '`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.',
        PydanticDeprecatedSince26,
        stacklevel=2,
    )
    return self.tuple_schema(schema)

```

### tuple_schema

```python
tuple_schema(schema: TupleSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a tuple schema e.g. `tuple[int, str, bool]` or `tuple[int, ...]`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `TupleSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def tuple_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a tuple schema e.g. `tuple[int,
    str, bool]` or `tuple[int, ...]`.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema: JsonSchemaValue = {'type': 'array'}
    if 'variadic_item_index' in schema:
        variadic_item_index = schema['variadic_item_index']
        if variadic_item_index > 0:
            json_schema['minItems'] = variadic_item_index
            json_schema['prefixItems'] = [
                self.generate_inner(item) for item in schema['items_schema'][:variadic_item_index]
            ]
        if variadic_item_index + 1 == len(schema['items_schema']):
            # if the variadic item is the last item, then represent it faithfully
            json_schema['items'] = self.generate_inner(schema['items_schema'][variadic_item_index])
        else:
            # otherwise, 'items' represents the schema for the variadic
            # item plus the suffix, so just allow anything for simplicity
            # for now
            json_schema['items'] = True
    else:
        prefixItems = [self.generate_inner(item) for item in schema['items_schema']]
        if prefixItems:
            json_schema['prefixItems'] = prefixItems
        json_schema['minItems'] = len(prefixItems)
        json_schema['maxItems'] = len(prefixItems)
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
    return json_schema

```

### set_schema

```python
set_schema(schema: SetSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a set schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `SetSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a set schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self._common_set_schema(schema)

```

### frozenset_schema

```python
frozenset_schema(
    schema: FrozenSetSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a frozenset schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `FrozenSetSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a frozenset schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self._common_set_schema(schema)

```

### generator_schema

```python
generator_schema(
    schema: GeneratorSchema,
) -> JsonSchemaValue

```

Returns a JSON schema that represents the provided GeneratorSchema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `GeneratorSchema` | The schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
    """Returns a JSON schema that represents the provided GeneratorSchema.

    Args:
        schema: The schema.

    Returns:
        The generated JSON schema.
    """
    items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
    json_schema = {'type': 'array', 'items': items_schema}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
    return json_schema

```

### dict_schema

```python
dict_schema(schema: DictSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a dict schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DictSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a dict schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema: JsonSchemaValue = {'type': 'object'}

    keys_schema = self.generate_inner(schema['keys_schema']).copy() if 'keys_schema' in schema else {}
    if '$ref' not in keys_schema:
        keys_pattern = keys_schema.pop('pattern', None)
        # Don't give a title to patternProperties/propertyNames:
        keys_schema.pop('title', None)
    else:
        # Here, we assume that if the keys schema is a definition reference,
        # it can't be a simple string core schema (and thus no pattern can exist).
        # However, this is only in practice (in theory, a definition reference core
        # schema could be generated for a simple string schema).
        # Note that we avoid calling `self.resolve_ref_schema`, as it might not exist yet.
        keys_pattern = None

    values_schema = self.generate_inner(schema['values_schema']).copy() if 'values_schema' in schema else {}
    # don't give a title to additionalProperties:
    values_schema.pop('title', None)

    if values_schema or keys_pattern is not None:
        if keys_pattern is None:
            json_schema['additionalProperties'] = values_schema
        else:
            json_schema['patternProperties'] = {keys_pattern: values_schema}
    else:  # for `dict[str, Any]`, we allow any key and any value, since `str` is the default key type
        json_schema['additionalProperties'] = True

    if (
        # The len check indicates that constraints are probably present:
        (keys_schema.get('type') == 'string' and len(keys_schema) > 1)
        # If this is a definition reference schema, it most likely has constraints:
        or '$ref' in keys_schema
    ):
        keys_schema.pop('type', None)
        json_schema['propertyNames'] = keys_schema

    self.update_with_validations(json_schema, schema, self.ValidationsMapping.object)
    return json_schema

```

### function_before_schema

```python
function_before_schema(
    schema: BeforeValidatorFunctionSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a function-before schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `BeforeValidatorFunctionSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def function_before_schema(self, schema: core_schema.BeforeValidatorFunctionSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a function-before schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    if self.mode == 'validation' and (input_schema := schema.get('json_schema_input_schema')):
        return self.generate_inner(input_schema)

    return self.generate_inner(schema['schema'])

```

### function_after_schema

```python
function_after_schema(
    schema: AfterValidatorFunctionSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a function-after schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `AfterValidatorFunctionSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def function_after_schema(self, schema: core_schema.AfterValidatorFunctionSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a function-after schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['schema'])

```

### function_plain_schema

```python
function_plain_schema(
    schema: PlainValidatorFunctionSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a function-plain schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `PlainValidatorFunctionSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def function_plain_schema(self, schema: core_schema.PlainValidatorFunctionSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a function-plain schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    if self.mode == 'validation' and (input_schema := schema.get('json_schema_input_schema')):
        return self.generate_inner(input_schema)

    return self.handle_invalid_for_json_schema(
        schema, f'core_schema.PlainValidatorFunctionSchema ({schema["function"]})'
    )

```

### function_wrap_schema

```python
function_wrap_schema(
    schema: WrapValidatorFunctionSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a function-wrap schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `WrapValidatorFunctionSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def function_wrap_schema(self, schema: core_schema.WrapValidatorFunctionSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a function-wrap schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    if self.mode == 'validation' and (input_schema := schema.get('json_schema_input_schema')):
        return self.generate_inner(input_schema)

    return self.generate_inner(schema['schema'])

```

### default_schema

```python
default_schema(
    schema: WithDefaultSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema with a default value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `WithDefaultSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema with a default value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema = self.generate_inner(schema['schema'])

    default = self.get_default_value(schema)
    if default is NoDefault or default is MISSING:
        return json_schema

    # we reflect the application of custom plain, no-info serializers to defaults for
    # JSON Schemas viewed in serialization mode:
    # TODO: improvements along with https://github.com/pydantic/pydantic/issues/8208
    if self.mode == 'serialization':
        # `_get_ser_schema_for_default_value()` is used to unpack potentially nested validator schemas:
        ser_schema = _get_ser_schema_for_default_value(schema['schema'])
        if (
            ser_schema is not None
            and (ser_func := ser_schema.get('function'))
            and not (default is None and ser_schema.get('when_used') in ('unless-none', 'json-unless-none'))
        ):
            try:
                default = ser_func(default)  # type: ignore
            except Exception:
                # It might be that the provided default needs to be validated (read: parsed) first
                # (assuming `validate_default` is enabled). However, we can't perform
                # such validation during JSON Schema generation so we don't support
                # this pattern for now.
                # (One example is when using `foo: ByteSize = '1MB'`, which validates and
                # serializes as an int. In this case, `ser_func` is `int` and `int('1MB')` fails).
                self.emit_warning(
                    'non-serializable-default',
                    f'Unable to serialize value {default!r} with the plain serializer; excluding default from JSON schema',
                )
                return json_schema

    try:
        encoded_default = self.encode_default(default)
    except pydantic_core.PydanticSerializationError:
        self.emit_warning(
            'non-serializable-default',
            f'Default value {default} is not JSON serializable; excluding default from JSON schema',
        )
        # Return the inner schema, as though there was no default
        return json_schema

    json_schema['default'] = encoded_default
    return json_schema

```

### get_default_value

```python
get_default_value(schema: WithDefaultSchema) -> Any

```

Get the default value to be used when generating a JSON Schema for a core schema with a default.

The default implementation is to use the statically defined default value. This method can be overridden if you want to make use of the default factory.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `WithDefaultSchema` | The 'with-default' core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | The default value to use, or NoDefault if no default value is available. |

Source code in `pydantic/json_schema.py`

```python
def get_default_value(self, schema: core_schema.WithDefaultSchema) -> Any:
    """Get the default value to be used when generating a JSON Schema for a core schema with a default.

    The default implementation is to use the statically defined default value. This method can be overridden
    if you want to make use of the default factory.

    Args:
        schema: The `'with-default'` core schema.

    Returns:
        The default value to use, or [`NoDefault`][pydantic.json_schema.NoDefault] if no default
            value is available.
    """
    return schema.get('default', NoDefault)

```

### nullable_schema

```python
nullable_schema(schema: NullableSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that allows null values.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `NullableSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that allows null values.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    null_schema = {'type': 'null'}
    inner_json_schema = self.generate_inner(schema['schema'])

    if inner_json_schema == null_schema:
        return null_schema
    else:
        # Thanks to the equality check against `null_schema` above, I think 'oneOf' would also be valid here;
        # I'll use 'anyOf' for now, but it could be changed it if it would work better with some external tooling
        return self.get_flattened_anyof([inner_json_schema, null_schema])

```

### union_schema

```python
union_schema(schema: UnionSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `UnionSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    generated: list[JsonSchemaValue] = []

    choices = schema['choices']
    for choice in choices:
        # choice will be a tuple if an explicit label was provided
        choice_schema = choice[0] if isinstance(choice, tuple) else choice
        try:
            generated.append(self.generate_inner(choice_schema))
        except PydanticOmit:
            continue
        except PydanticInvalidForJsonSchema as exc:
            self.emit_warning('skipped-choice', exc.message)
    if len(generated) == 1:
        return generated[0]
    return self.get_flattened_anyof(generated)

```

### tagged_union_schema

```python
tagged_union_schema(
    schema: TaggedUnionSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that allows values matching any of the given schemas, where the schemas are tagged with a discriminator field that indicates which schema should be used to validate the value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `TaggedUnionSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that allows values matching any of the given schemas, where
    the schemas are tagged with a discriminator field that indicates which schema should be used to validate
    the value.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    generated: dict[str, JsonSchemaValue] = {}
    for k, v in schema['choices'].items():
        if isinstance(k, Enum):
            k = k.value
        try:
            # Use str(k) since keys must be strings for json; while not technically correct,
            # it's the closest that can be represented in valid JSON
            generated[str(k)] = self.generate_inner(v).copy()
        except PydanticOmit:
            continue
        except PydanticInvalidForJsonSchema as exc:
            self.emit_warning('skipped-choice', exc.message)

    one_of_choices = _deduplicate_schemas(generated.values())
    json_schema: JsonSchemaValue = {'oneOf': one_of_choices}

    # This reflects the v1 behavior; TODO: we should make it possible to exclude OpenAPI stuff from the JSON schema
    openapi_discriminator = self._extract_discriminator(schema, one_of_choices)
    if openapi_discriminator is not None:
        json_schema['discriminator'] = {
            'propertyName': openapi_discriminator,
            'mapping': {k: v.get('$ref', v) for k, v in generated.items()},
        }

    return json_schema

```

### chain_schema

```python
chain_schema(schema: ChainSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a core_schema.ChainSchema.

When generating a schema for validation, we return the validation JSON schema for the first step in the chain. For serialization, we return the serialization JSON schema for the last step in the chain.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ChainSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a core_schema.ChainSchema.

    When generating a schema for validation, we return the validation JSON schema for the first step in the chain.
    For serialization, we return the serialization JSON schema for the last step in the chain.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    step_index = 0 if self.mode == 'validation' else -1  # use first step for validation, last for serialization
    return self.generate_inner(schema['steps'][step_index])

```

### lax_or_strict_schema

```python
lax_or_strict_schema(
    schema: LaxOrStrictSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that allows values matching either the lax schema or the strict schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `LaxOrStrictSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that allows values matching either the lax schema or the
    strict schema.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    # TODO: Need to read the default value off of model config or whatever
    use_strict = schema.get('strict', False)  # TODO: replace this default False
    # If your JSON schema fails to generate it is probably
    # because one of the following two branches failed.
    if use_strict:
        return self.generate_inner(schema['strict_schema'])
    else:
        return self.generate_inner(schema['lax_schema'])

```

### json_or_python_schema

```python
json_or_python_schema(
    schema: JsonOrPythonSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that allows values matching either the JSON schema or the Python schema.

The JSON schema is used instead of the Python schema. If you want to use the Python schema, you should override this method.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `JsonOrPythonSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def json_or_python_schema(self, schema: core_schema.JsonOrPythonSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that allows values matching either the JSON schema or the
    Python schema.

    The JSON schema is used instead of the Python schema. If you want to use the Python schema, you should override
    this method.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['json_schema'])

```

### typed_dict_schema

```python
typed_dict_schema(
    schema: TypedDictSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a typed dict.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `TypedDictSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a typed dict.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    total = schema.get('total', True)
    named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
        (name, self.field_is_required(field, total), field)
        for name, field in schema['fields'].items()
        if self.field_is_present(field)
    ]
    if self.mode == 'serialization':
        named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
    cls = schema.get('cls')
    config = _get_typed_dict_config(cls)
    with self._config_wrapper_stack.push(config):
        json_schema = self._named_required_fields_schema(named_required_fields)

    if cls is not None:
        self._update_class_schema(json_schema, cls, config)
    else:
        extra = config.get('extra')
        if extra == 'forbid':
            json_schema['additionalProperties'] = False
        elif extra == 'allow':
            json_schema['additionalProperties'] = True

    return json_schema

```

### typed_dict_field_schema

```python
typed_dict_field_schema(
    schema: TypedDictField,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a typed dict field.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `TypedDictField` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def typed_dict_field_schema(self, schema: core_schema.TypedDictField) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a typed dict field.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['schema'])

```

### dataclass_field_schema

```python
dataclass_field_schema(
    schema: DataclassField,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a dataclass field.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DataclassField` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def dataclass_field_schema(self, schema: core_schema.DataclassField) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a dataclass field.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['schema'])

```

### model_field_schema

```python
model_field_schema(schema: ModelField) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a model field.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ModelField` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def model_field_schema(self, schema: core_schema.ModelField) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a model field.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['schema'])

```

### computed_field_schema

```python
computed_field_schema(
    schema: ComputedField,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a computed field.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ComputedField` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def computed_field_schema(self, schema: core_schema.ComputedField) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a computed field.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['return_schema'])

```

### model_schema

```python
model_schema(schema: ModelSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ModelSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a model.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    # We do not use schema['model'].model_json_schema() here
    # because it could lead to inconsistent refs handling, etc.
    cls = cast('type[BaseModel]', schema['cls'])
    config = cls.model_config

    with self._config_wrapper_stack.push(config):
        json_schema = self.generate_inner(schema['schema'])

    self._update_class_schema(json_schema, cls, config)

    return json_schema

```

### resolve_ref_schema

```python
resolve_ref_schema(
    json_schema: JsonSchemaValue,
) -> JsonSchemaValue

```

Resolve a JsonSchemaValue to the non-ref schema if it is a $ref schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `json_schema` | `JsonSchemaValue` | The schema to resolve. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The resolved schema. |

Raises:

| Type | Description | | --- | --- | | `RuntimeError` | If the schema reference can't be found in definitions. |

Source code in `pydantic/json_schema.py`

```python
def resolve_ref_schema(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
    """Resolve a JsonSchemaValue to the non-ref schema if it is a $ref schema.

    Args:
        json_schema: The schema to resolve.

    Returns:
        The resolved schema.

    Raises:
        RuntimeError: If the schema reference can't be found in definitions.
    """
    while '$ref' in json_schema:
        ref = json_schema['$ref']
        schema_to_update = self.get_schema_from_definitions(JsonRef(ref))
        if schema_to_update is None:
            raise RuntimeError(f'Cannot update undefined schema for $ref={ref}')
        json_schema = schema_to_update
    return json_schema

```

### model_fields_schema

```python
model_fields_schema(
    schema: ModelFieldsSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a model's fields.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ModelFieldsSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def model_fields_schema(self, schema: core_schema.ModelFieldsSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a model's fields.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
        (name, self.field_is_required(field, total=True), field)
        for name, field in schema['fields'].items()
        if self.field_is_present(field)
    ]
    if self.mode == 'serialization':
        named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
    json_schema = self._named_required_fields_schema(named_required_fields)
    extras_schema = schema.get('extras_schema', None)
    if extras_schema is not None:
        schema_to_update = self.resolve_ref_schema(json_schema)
        schema_to_update['additionalProperties'] = self.generate_inner(extras_schema)
    return json_schema

```

### field_is_present

```python
field_is_present(field: CoreSchemaField) -> bool

```

Whether the field should be included in the generated JSON schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `CoreSchemaField` | The schema for the field itself. | *required* |

Returns:

| Type | Description | | --- | --- | | `bool` | True if the field should be included in the generated JSON schema, False otherwise. |

Source code in `pydantic/json_schema.py`

```python
def field_is_present(self, field: CoreSchemaField) -> bool:
    """Whether the field should be included in the generated JSON schema.

    Args:
        field: The schema for the field itself.

    Returns:
        `True` if the field should be included in the generated JSON schema, `False` otherwise.
    """
    if self.mode == 'serialization':
        # If you still want to include the field in the generated JSON schema,
        # override this method and return True
        return not field.get('serialization_exclude')
    elif self.mode == 'validation':
        return True
    else:
        assert_never(self.mode)

```

### field_is_required

```python
field_is_required(
    field: ModelField | DataclassField | TypedDictField,
    total: bool,
) -> bool

```

Whether the field should be marked as required in the generated JSON schema. (Note that this is irrelevant if the field is not present in the JSON schema.).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `ModelField | DataclassField | TypedDictField` | The schema for the field itself. | *required* | | `total` | `bool` | Only applies to TypedDictFields. Indicates if the TypedDict this field belongs to is total, in which case any fields that don't explicitly specify required=False are required. | *required* |

Returns:

| Type | Description | | --- | --- | | `bool` | True if the field should be marked as required in the generated JSON schema, False otherwise. |

Source code in `pydantic/json_schema.py`

```python
def field_is_required(
    self,
    field: core_schema.ModelField | core_schema.DataclassField | core_schema.TypedDictField,
    total: bool,
) -> bool:
    """Whether the field should be marked as required in the generated JSON schema.
    (Note that this is irrelevant if the field is not present in the JSON schema.).

    Args:
        field: The schema for the field itself.
        total: Only applies to `TypedDictField`s.
            Indicates if the `TypedDict` this field belongs to is total, in which case any fields that don't
            explicitly specify `required=False` are required.

    Returns:
        `True` if the field should be marked as required in the generated JSON schema, `False` otherwise.
    """
    if self.mode == 'serialization' and self._config.json_schema_serialization_defaults_required:
        return not field.get('serialization_exclude')
    else:
        if field['type'] == 'typed-dict-field':
            return field.get('required', total)
        else:
            return field['schema']['type'] != 'default'

```

### dataclass_args_schema

```python
dataclass_args_schema(
    schema: DataclassArgsSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a dataclass's constructor arguments.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DataclassArgsSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def dataclass_args_schema(self, schema: core_schema.DataclassArgsSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a dataclass's constructor arguments.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
        (field['name'], self.field_is_required(field, total=True), field)
        for field in schema['fields']
        if self.field_is_present(field)
    ]
    if self.mode == 'serialization':
        named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
    return self._named_required_fields_schema(named_required_fields)

```

### dataclass_schema

```python
dataclass_schema(
    schema: DataclassSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a dataclass.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DataclassSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a dataclass.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    from ._internal._dataclasses import is_stdlib_dataclass

    cls = schema['cls']
    config: ConfigDict = getattr(cls, '__pydantic_config__', cast('ConfigDict', {}))

    with self._config_wrapper_stack.push(config):
        json_schema = self.generate_inner(schema['schema']).copy()

    self._update_class_schema(json_schema, cls, config)

    # Dataclass-specific handling of description
    if is_stdlib_dataclass(cls):
        # vanilla dataclass; don't use cls.__doc__ as it will contain the class signature by default
        description = None
    else:
        description = None if cls.__doc__ is None else inspect.cleandoc(cls.__doc__)
    if description:
        json_schema['description'] = description

    return json_schema

```

### arguments_schema

```python
arguments_schema(
    schema: ArgumentsSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a function's arguments.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ArgumentsSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a function's arguments.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    prefer_positional = schema.get('metadata', {}).get('pydantic_js_prefer_positional_arguments')

    arguments = schema['arguments_schema']
    kw_only_arguments = [a for a in arguments if a.get('mode') == 'keyword_only']
    kw_or_p_arguments = [a for a in arguments if a.get('mode') in {'positional_or_keyword', None}]
    p_only_arguments = [a for a in arguments if a.get('mode') == 'positional_only']
    var_args_schema = schema.get('var_args_schema')
    var_kwargs_schema = schema.get('var_kwargs_schema')

    if prefer_positional:
        positional_possible = not kw_only_arguments and not var_kwargs_schema
        if positional_possible:
            return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

    keyword_possible = not p_only_arguments and not var_args_schema
    if keyword_possible:
        return self.kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_kwargs_schema)

    if not prefer_positional:
        positional_possible = not kw_only_arguments and not var_kwargs_schema
        if positional_possible:
            return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

    raise PydanticInvalidForJsonSchema(
        'Unable to generate JSON schema for arguments validator with positional-only and keyword-only arguments'
    )

```

### kw_arguments_schema

```python
kw_arguments_schema(
    arguments: list[ArgumentsParameter],
    var_kwargs_schema: CoreSchema | None,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a function's keyword arguments.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `arguments` | `list[ArgumentsParameter]` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def kw_arguments_schema(
    self, arguments: list[core_schema.ArgumentsParameter], var_kwargs_schema: CoreSchema | None
) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a function's keyword arguments.

    Args:
        arguments: The core schema.

    Returns:
        The generated JSON schema.
    """
    properties: dict[str, JsonSchemaValue] = {}
    required: list[str] = []
    for argument in arguments:
        name = self.get_argument_name(argument)
        argument_schema = self.generate_inner(argument['schema']).copy()
        if 'title' not in argument_schema and self.field_title_should_be_set(argument['schema']):
            argument_schema['title'] = self.get_title_from_name(name)
        properties[name] = argument_schema

        if argument['schema']['type'] != 'default':
            # This assumes that if the argument has a default value,
            # the inner schema must be of type WithDefaultSchema.
            # I believe this is true, but I am not 100% sure
            required.append(name)

    json_schema: JsonSchemaValue = {'type': 'object', 'properties': properties}
    if required:
        json_schema['required'] = required

    if var_kwargs_schema:
        additional_properties_schema = self.generate_inner(var_kwargs_schema)
        if additional_properties_schema:
            json_schema['additionalProperties'] = additional_properties_schema
    else:
        json_schema['additionalProperties'] = False
    return json_schema

```

### p_arguments_schema

```python
p_arguments_schema(
    arguments: list[ArgumentsParameter],
    var_args_schema: CoreSchema | None,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a function's positional arguments.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `arguments` | `list[ArgumentsParameter]` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def p_arguments_schema(
    self, arguments: list[core_schema.ArgumentsParameter], var_args_schema: CoreSchema | None
) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a function's positional arguments.

    Args:
        arguments: The core schema.

    Returns:
        The generated JSON schema.
    """
    prefix_items: list[JsonSchemaValue] = []
    min_items = 0

    for argument in arguments:
        name = self.get_argument_name(argument)

        argument_schema = self.generate_inner(argument['schema']).copy()
        if 'title' not in argument_schema and self.field_title_should_be_set(argument['schema']):
            argument_schema['title'] = self.get_title_from_name(name)
        prefix_items.append(argument_schema)

        if argument['schema']['type'] != 'default':
            # This assumes that if the argument has a default value,
            # the inner schema must be of type WithDefaultSchema.
            # I believe this is true, but I am not 100% sure
            min_items += 1

    json_schema: JsonSchemaValue = {'type': 'array'}
    if prefix_items:
        json_schema['prefixItems'] = prefix_items
    if min_items:
        json_schema['minItems'] = min_items

    if var_args_schema:
        items_schema = self.generate_inner(var_args_schema)
        if items_schema:
            json_schema['items'] = items_schema
    else:
        json_schema['maxItems'] = len(prefix_items)

    return json_schema

```

### get_argument_name

```python
get_argument_name(
    argument: ArgumentsParameter | ArgumentsV3Parameter,
) -> str

```

Retrieves the name of an argument.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `argument` | `ArgumentsParameter | ArgumentsV3Parameter` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `str` | The name of the argument. |

Source code in `pydantic/json_schema.py`

```python
def get_argument_name(self, argument: core_schema.ArgumentsParameter | core_schema.ArgumentsV3Parameter) -> str:
    """Retrieves the name of an argument.

    Args:
        argument: The core schema.

    Returns:
        The name of the argument.
    """
    name = argument['name']
    if self.by_alias:
        alias = argument.get('alias')
        if isinstance(alias, str):
            name = alias
        else:
            pass  # might want to do something else?
    return name

```

### arguments_v3_schema

```python
arguments_v3_schema(
    schema: ArgumentsV3Schema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a function's arguments.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ArgumentsV3Schema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def arguments_v3_schema(self, schema: core_schema.ArgumentsV3Schema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a function's arguments.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    arguments = schema['arguments_schema']
    properties: dict[str, JsonSchemaValue] = {}
    required: list[str] = []
    for argument in arguments:
        mode = argument.get('mode', 'positional_or_keyword')
        name = self.get_argument_name(argument)
        argument_schema = self.generate_inner(argument['schema']).copy()
        if mode == 'var_args':
            argument_schema = {'type': 'array', 'items': argument_schema}
        elif mode == 'var_kwargs_uniform':
            argument_schema = {'type': 'object', 'additionalProperties': argument_schema}

        argument_schema.setdefault('title', self.get_title_from_name(name))
        properties[name] = argument_schema

        if (
            (mode == 'var_kwargs_unpacked_typed_dict' and 'required' in argument_schema)
            or mode not in {'var_args', 'var_kwargs_uniform', 'var_kwargs_unpacked_typed_dict'}
            and argument['schema']['type'] != 'default'
        ):
            # This assumes that if the argument has a default value,
            # the inner schema must be of type WithDefaultSchema.
            # I believe this is true, but I am not 100% sure
            required.append(name)

    json_schema: JsonSchemaValue = {'type': 'object', 'properties': properties}
    if required:
        json_schema['required'] = required
    return json_schema

```

### call_schema

```python
call_schema(schema: CallSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a function call.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CallSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a function call.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['arguments_schema'])

```

### custom_error_schema

```python
custom_error_schema(
    schema: CustomErrorSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a custom error.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CustomErrorSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a custom error.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return self.generate_inner(schema['schema'])

```

### json_schema

```python
json_schema(schema: JsonSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a JSON object.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `JsonSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a JSON object.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    content_core_schema = schema.get('schema') or core_schema.any_schema()
    content_json_schema = self.generate_inner(content_core_schema)
    if self.mode == 'validation':
        return {'type': 'string', 'contentMediaType': 'application/json', 'contentSchema': content_json_schema}
    else:
        # self.mode == 'serialization'
        return content_json_schema

```

### url_schema

```python
url_schema(schema: UrlSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a URL.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `UrlSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a URL.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
    return json_schema

```

### multi_host_url_schema

```python
multi_host_url_schema(
    schema: MultiHostUrlSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a URL that can be used with multiple hosts.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `MultiHostUrlSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a URL that can be used with multiple hosts.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    # Note: 'multi-host-uri' is a custom/pydantic-specific format, not part of the JSON Schema spec
    json_schema = {'type': 'string', 'format': 'multi-host-uri', 'minLength': 1}
    self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
    return json_schema

```

### uuid_schema

```python
uuid_schema(schema: UuidSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a UUID.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `UuidSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def uuid_schema(self, schema: core_schema.UuidSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a UUID.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'string', 'format': 'uuid'}

```

### definitions_schema

```python
definitions_schema(
    schema: DefinitionsSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that defines a JSON object with definitions.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DefinitionsSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def definitions_schema(self, schema: core_schema.DefinitionsSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that defines a JSON object with definitions.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    for definition in schema['definitions']:
        try:
            self.generate_inner(definition)
        except PydanticInvalidForJsonSchema as e:  # noqa: PERF203
            core_ref: CoreRef = CoreRef(definition['ref'])  # type: ignore
            self._core_defs_invalid_for_json_schema[self.get_defs_ref((core_ref, self.mode))] = e
            continue
    return self.generate_inner(schema['schema'])

```

### definition_ref_schema

```python
definition_ref_schema(
    schema: DefinitionReferenceSchema,
) -> JsonSchemaValue

```

Generates a JSON schema that matches a schema that references a definition.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `DefinitionReferenceSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def definition_ref_schema(self, schema: core_schema.DefinitionReferenceSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a schema that references a definition.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    core_ref = CoreRef(schema['schema_ref'])
    _, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
    return ref_json_schema

```

### ser_schema

```python
ser_schema(
    schema: (
        SerSchema | IncExSeqSerSchema | IncExDictSerSchema
    ),
) -> JsonSchemaValue | None

```

Generates a JSON schema that matches a schema that defines a serialized object.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `SerSchema | IncExSeqSerSchema | IncExDictSerSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue | None` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def ser_schema(
    self, schema: core_schema.SerSchema | core_schema.IncExSeqSerSchema | core_schema.IncExDictSerSchema
) -> JsonSchemaValue | None:
    """Generates a JSON schema that matches a schema that defines a serialized object.

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    schema_type = schema['type']
    if schema_type == 'function-plain' or schema_type == 'function-wrap':
        # PlainSerializerFunctionSerSchema or WrapSerializerFunctionSerSchema
        return_schema = schema.get('return_schema')
        if return_schema is not None:
            return self.generate_inner(return_schema)
    elif schema_type == 'format' or schema_type == 'to-string':
        # FormatSerSchema or ToStringSerSchema
        return self.str_schema(core_schema.str_schema())
    elif schema['type'] == 'model':
        # ModelSerSchema
        return self.generate_inner(schema['schema'])
    return None

```

### complex_schema

```python
complex_schema(schema: ComplexSchema) -> JsonSchemaValue

```

Generates a JSON schema that matches a complex number.

JSON has no standard way to represent complex numbers. Complex number is not a numeric type. Here we represent complex number as strings following the rule defined by Python. For instance, '1+2j' is an accepted complex string. Details can be found in Python's complex documentation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `ComplexSchema` | The core schema. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The generated JSON schema. |

Source code in `pydantic/json_schema.py`

```python
def complex_schema(self, schema: core_schema.ComplexSchema) -> JsonSchemaValue:
    """Generates a JSON schema that matches a complex number.

    JSON has no standard way to represent complex numbers. Complex number is not a numeric
    type. Here we represent complex number as strings following the rule defined by Python.
    For instance, '1+2j' is an accepted complex string. Details can be found in
    [Python's `complex` documentation][complex].

    Args:
        schema: The core schema.

    Returns:
        The generated JSON schema.
    """
    return {'type': 'string'}

```

### get_title_from_name

```python
get_title_from_name(name: str) -> str

```

Retrieves a title from a name.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name to retrieve a title from. | *required* |

Returns:

| Type | Description | | --- | --- | | `str` | The title. |

Source code in `pydantic/json_schema.py`

```python
def get_title_from_name(self, name: str) -> str:
    """Retrieves a title from a name.

    Args:
        name: The name to retrieve a title from.

    Returns:
        The title.
    """
    return name.title().replace('_', ' ').strip()

```

### field_title_should_be_set

```python
field_title_should_be_set(
    schema: CoreSchemaOrField,
) -> bool

```

Returns true if a field with the given schema should have a title set based on the field name.

Intuitively, we want this to return true for schemas that wouldn't otherwise provide their own title (e.g., int, float, str), and false for those that would (e.g., BaseModel subclasses).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchemaOrField` | The schema to check. | *required* |

Returns:

| Type | Description | | --- | --- | | `bool` | True if the field should have a title set, False otherwise. |

Source code in `pydantic/json_schema.py`

```python
def field_title_should_be_set(self, schema: CoreSchemaOrField) -> bool:
    """Returns true if a field with the given schema should have a title set based on the field name.

    Intuitively, we want this to return true for schemas that wouldn't otherwise provide their own title
    (e.g., int, float, str), and false for those that would (e.g., BaseModel subclasses).

    Args:
        schema: The schema to check.

    Returns:
        `True` if the field should have a title set, `False` otherwise.
    """
    if _core_utils.is_core_schema_field(schema):
        if schema['type'] == 'computed-field':
            field_schema = schema['return_schema']
        else:
            field_schema = schema['schema']
        return self.field_title_should_be_set(field_schema)

    elif _core_utils.is_core_schema(schema):
        if schema.get('ref'):  # things with refs, such as models and enums, should not have titles set
            return False
        if schema['type'] in {'default', 'nullable', 'definitions'}:
            return self.field_title_should_be_set(schema['schema'])  # type: ignore[typeddict-item]
        if _core_utils.is_function_with_inner_schema(schema):
            return self.field_title_should_be_set(schema['schema'])
        if schema['type'] == 'definition-ref':
            # Referenced schemas should not have titles set for the same reason
            # schemas with refs should not
            return False
        return True  # anything else should have title set

    else:
        raise PydanticInvalidForJsonSchema(f'Unexpected schema type: schema={schema}')  # pragma: no cover

```

### normalize_name

```python
normalize_name(name: str) -> str

```

Normalizes a name to be used as a key in a dictionary.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name to normalize. | *required* |

Returns:

| Type | Description | | --- | --- | | `str` | The normalized name. |

Source code in `pydantic/json_schema.py`

```python
def normalize_name(self, name: str) -> str:
    """Normalizes a name to be used as a key in a dictionary.

    Args:
        name: The name to normalize.

    Returns:
        The normalized name.
    """
    return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name).replace('.', '__')

```

### get_defs_ref

```python
get_defs_ref(core_mode_ref: CoreModeRef) -> DefsRef

```

Override this method to change the way that definitions keys are generated from a core reference.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `core_mode_ref` | `CoreModeRef` | The core reference. | *required* |

Returns:

| Type | Description | | --- | --- | | `DefsRef` | The definitions key. |

Source code in `pydantic/json_schema.py`

```python
def get_defs_ref(self, core_mode_ref: CoreModeRef) -> DefsRef:
    """Override this method to change the way that definitions keys are generated from a core reference.

    Args:
        core_mode_ref: The core reference.

    Returns:
        The definitions key.
    """
    # Split the core ref into "components"; generic origins and arguments are each separate components
    core_ref, mode = core_mode_ref
    components = re.split(r'([\][,])', core_ref)
    # Remove IDs from each component
    components = [x.rsplit(':', 1)[0] for x in components]
    core_ref_no_id = ''.join(components)
    # Remove everything before the last period from each "component"
    components = [re.sub(r'(?:[^.[\]]+\.)+((?:[^.[\]]+))', r'\1', x) for x in components]
    short_ref = ''.join(components)

    mode_title = _MODE_TITLE_MAPPING[mode]

    # It is important that the generated defs_ref values be such that at least one choice will not
    # be generated for any other core_ref. Currently, this should be the case because we include
    # the id of the source type in the core_ref
    name = DefsRef(self.normalize_name(short_ref))
    name_mode = DefsRef(self.normalize_name(short_ref) + f'-{mode_title}')
    module_qualname = DefsRef(self.normalize_name(core_ref_no_id))
    module_qualname_mode = DefsRef(f'{module_qualname}-{mode_title}')
    module_qualname_id = DefsRef(self.normalize_name(core_ref))
    occurrence_index = self._collision_index.get(module_qualname_id)
    if occurrence_index is None:
        self._collision_counter[module_qualname] += 1
        occurrence_index = self._collision_index[module_qualname_id] = self._collision_counter[module_qualname]

    module_qualname_occurrence = DefsRef(f'{module_qualname}__{occurrence_index}')
    module_qualname_occurrence_mode = DefsRef(f'{module_qualname_mode}__{occurrence_index}')

    self._prioritized_defsref_choices[module_qualname_occurrence_mode] = [
        name,
        name_mode,
        module_qualname,
        module_qualname_mode,
        module_qualname_occurrence,
        module_qualname_occurrence_mode,
    ]

    return module_qualname_occurrence_mode

```

### get_cache_defs_ref_schema

```python
get_cache_defs_ref_schema(
    core_ref: CoreRef,
) -> tuple[DefsRef, JsonSchemaValue]

```

This method wraps the get_defs_ref method with some cache-lookup/population logic, and returns both the produced defs_ref and the JSON schema that will refer to the right definition.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `core_ref` | `CoreRef` | The core reference to get the definitions reference for. | *required* |

Returns:

| Type | Description | | --- | --- | | `tuple[DefsRef, JsonSchemaValue]` | A tuple of the definitions reference and the JSON schema that will refer to it. |

Source code in `pydantic/json_schema.py`

```python
def get_cache_defs_ref_schema(self, core_ref: CoreRef) -> tuple[DefsRef, JsonSchemaValue]:
    """This method wraps the get_defs_ref method with some cache-lookup/population logic,
    and returns both the produced defs_ref and the JSON schema that will refer to the right definition.

    Args:
        core_ref: The core reference to get the definitions reference for.

    Returns:
        A tuple of the definitions reference and the JSON schema that will refer to it.
    """
    core_mode_ref = (core_ref, self.mode)
    maybe_defs_ref = self.core_to_defs_refs.get(core_mode_ref)
    if maybe_defs_ref is not None:
        json_ref = self.core_to_json_refs[core_mode_ref]
        return maybe_defs_ref, {'$ref': json_ref}

    defs_ref = self.get_defs_ref(core_mode_ref)

    # populate the ref translation mappings
    self.core_to_defs_refs[core_mode_ref] = defs_ref
    self.defs_to_core_refs[defs_ref] = core_mode_ref

    json_ref = JsonRef(self.ref_template.format(model=defs_ref))
    self.core_to_json_refs[core_mode_ref] = json_ref
    self.json_to_defs_refs[json_ref] = defs_ref
    ref_json_schema = {'$ref': json_ref}
    return defs_ref, ref_json_schema

```

### handle_ref_overrides

```python
handle_ref_overrides(
    json_schema: JsonSchemaValue,
) -> JsonSchemaValue

```

Remove any sibling keys that are redundant with the referenced schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `json_schema` | `JsonSchemaValue` | The schema to remove redundant sibling keys from. | *required* |

Returns:

| Type | Description | | --- | --- | | `JsonSchemaValue` | The schema with redundant sibling keys removed. |

Source code in `pydantic/json_schema.py`

```python
def handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
    """Remove any sibling keys that are redundant with the referenced schema.

    Args:
        json_schema: The schema to remove redundant sibling keys from.

    Returns:
        The schema with redundant sibling keys removed.
    """
    if '$ref' in json_schema:
        # prevent modifications to the input; this copy may be safe to drop if there is significant overhead
        json_schema = json_schema.copy()

        referenced_json_schema = self.get_schema_from_definitions(JsonRef(json_schema['$ref']))
        if referenced_json_schema is None:
            # This can happen when building schemas for models with not-yet-defined references.
            # It may be a good idea to do a recursive pass at the end of the generation to remove
            # any redundant override keys.
            return json_schema
        for k, v in list(json_schema.items()):
            if k == '$ref':
                continue
            if k in referenced_json_schema and referenced_json_schema[k] == v:
                del json_schema[k]  # redundant key

    return json_schema

```

### encode_default

```python
encode_default(dft: Any) -> Any

```

Encode a default value to a JSON-serializable value.

This is used to encode default values for fields in the generated JSON schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `dft` | `Any` | The default value to encode. | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | The encoded default value. |

Source code in `pydantic/json_schema.py`

```python
def encode_default(self, dft: Any) -> Any:
    """Encode a default value to a JSON-serializable value.

    This is used to encode default values for fields in the generated JSON schema.

    Args:
        dft: The default value to encode.

    Returns:
        The encoded default value.
    """
    from .type_adapter import TypeAdapter, _type_has_config

    config = self._config
    try:
        default = (
            dft
            if _type_has_config(type(dft))
            else TypeAdapter(type(dft), config=config.config_dict).dump_python(
                dft, by_alias=self.by_alias, mode='json'
            )
        )
    except PydanticSchemaGenerationError:
        raise pydantic_core.PydanticSerializationError(f'Unable to encode default value {dft}')

    return pydantic_core.to_jsonable_python(
        default, timedelta_mode=config.ser_json_timedelta, bytes_mode=config.ser_json_bytes, by_alias=self.by_alias
    )

```

### update_with_validations

```python
update_with_validations(
    json_schema: JsonSchemaValue,
    core_schema: CoreSchema,
    mapping: dict[str, str],
) -> None

```

Update the json_schema with the corresponding validations specified in the core_schema, using the provided mapping to translate keys in core_schema to the appropriate keys for a JSON schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `json_schema` | `JsonSchemaValue` | The JSON schema to update. | *required* | | `core_schema` | `CoreSchema` | The core schema to get the validations from. | *required* | | `mapping` | `dict[str, str]` | A mapping from core_schema attribute names to the corresponding JSON schema attribute names. | *required* |

Source code in `pydantic/json_schema.py`

```python
def update_with_validations(
    self, json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: dict[str, str]
) -> None:
    """Update the json_schema with the corresponding validations specified in the core_schema,
    using the provided mapping to translate keys in core_schema to the appropriate keys for a JSON schema.

    Args:
        json_schema: The JSON schema to update.
        core_schema: The core schema to get the validations from.
        mapping: A mapping from core_schema attribute names to the corresponding JSON schema attribute names.
    """
    for core_key, json_schema_key in mapping.items():
        if core_key in core_schema:
            json_schema[json_schema_key] = core_schema[core_key]

```

### get_json_ref_counts

```python
get_json_ref_counts(
    json_schema: JsonSchemaValue,
) -> dict[JsonRef, int]

```

Get all values corresponding to the key '$ref' anywhere in the json_schema.

Source code in `pydantic/json_schema.py`

```python
def get_json_ref_counts(self, json_schema: JsonSchemaValue) -> dict[JsonRef, int]:
    """Get all values corresponding to the key '$ref' anywhere in the json_schema."""
    json_refs: dict[JsonRef, int] = Counter()

    def _add_json_refs(schema: Any) -> None:
        if isinstance(schema, dict):
            if '$ref' in schema:
                json_ref = JsonRef(schema['$ref'])
                if not isinstance(json_ref, str):
                    return  # in this case, '$ref' might have been the name of a property
                already_visited = json_ref in json_refs
                json_refs[json_ref] += 1
                if already_visited:
                    return  # prevent recursion on a definition that was already visited
                try:
                    defs_ref = self.json_to_defs_refs[json_ref]
                    if defs_ref in self._core_defs_invalid_for_json_schema:
                        raise self._core_defs_invalid_for_json_schema[defs_ref]
                    _add_json_refs(self.definitions[defs_ref])
                except KeyError:
                    if not json_ref.startswith(('http://', 'https://')):
                        raise

            for k, v in schema.items():
                if k == 'examples' and isinstance(v, list):
                    # Skip examples that may contain arbitrary values and references
                    # (see the comment in `_get_all_json_refs` for more details).
                    continue
                _add_json_refs(v)
        elif isinstance(schema, list):
            for v in schema:
                _add_json_refs(v)

    _add_json_refs(json_schema)
    return json_refs

```

### emit_warning

```python
emit_warning(
    kind: JsonSchemaWarningKind, detail: str
) -> None

```

This method simply emits PydanticJsonSchemaWarnings based on handling in the `warning_message` method.

Source code in `pydantic/json_schema.py`

```python
def emit_warning(self, kind: JsonSchemaWarningKind, detail: str) -> None:
    """This method simply emits PydanticJsonSchemaWarnings based on handling in the `warning_message` method."""
    message = self.render_warning_message(kind, detail)
    if message is not None:
        warnings.warn(message, PydanticJsonSchemaWarning)

```

### render_warning_message

```python
render_warning_message(
    kind: JsonSchemaWarningKind, detail: str
) -> str | None

```

This method is responsible for ignoring warnings as desired, and for formatting the warning messages.

You can override the value of `ignored_warning_kinds` in a subclass of GenerateJsonSchema to modify what warnings are generated. If you want more control, you can override this method; just return None in situations where you don't want warnings to be emitted.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `kind` | `JsonSchemaWarningKind` | The kind of warning to render. It can be one of the following: 'skipped-choice': A choice field was skipped because it had no valid choices. 'non-serializable-default': A default value was skipped because it was not JSON-serializable. | *required* | | `detail` | `str` | A string with additional details about the warning. | *required* |

Returns:

| Type | Description | | --- | --- | | `str | None` | The formatted warning message, or None if no warning should be emitted. |

Source code in `pydantic/json_schema.py`

```python
def render_warning_message(self, kind: JsonSchemaWarningKind, detail: str) -> str | None:
    """This method is responsible for ignoring warnings as desired, and for formatting the warning messages.

    You can override the value of `ignored_warning_kinds` in a subclass of GenerateJsonSchema
    to modify what warnings are generated. If you want more control, you can override this method;
    just return None in situations where you don't want warnings to be emitted.

    Args:
        kind: The kind of warning to render. It can be one of the following:

            - 'skipped-choice': A choice field was skipped because it had no valid choices.
            - 'non-serializable-default': A default value was skipped because it was not JSON-serializable.
        detail: A string with additional details about the warning.

    Returns:
        The formatted warning message, or `None` if no warning should be emitted.
    """
    if kind in self.ignored_warning_kinds:
        return None
    return f'{detail} [{kind}]'

```

## WithJsonSchema

```python
WithJsonSchema(
    json_schema: JsonSchemaValue | None,
    mode: (
        Literal["validation", "serialization"] | None
    ) = None,
)

```

Usage Documentation

[`WithJsonSchema` Annotation](../../concepts/json_schema/#withjsonschema-annotation)

Add this as an annotation on a field to override the (base) JSON schema that would be generated for that field. This provides a way to set a JSON schema for types that would otherwise raise errors when producing a JSON schema, such as Callable, or types that have an is-instance core schema, without needing to go so far as creating a custom subclass of pydantic.json_schema.GenerateJsonSchema. Note that any *modifications* to the schema that would normally be made (such as setting the title for model fields) will still be performed.

If `mode` is set this will only apply to that schema generation mode, allowing you to set different json schemas for validation and serialization.

## Examples

```python
Examples(
    examples: dict[str, Any],
    mode: (
        Literal["validation", "serialization"] | None
    ) = None,
)

```

```python
Examples(
    examples: list[Any],
    mode: (
        Literal["validation", "serialization"] | None
    ) = None,
)

```

```python
Examples(
    examples: dict[str, Any] | list[Any],
    mode: (
        Literal["validation", "serialization"] | None
    ) = None,
)

```

Add examples to a JSON schema.

If the JSON Schema already contains examples, the provided examples will be appended.

If `mode` is set this will only apply to that schema generation mode, allowing you to add different examples for validation and serialization.

Source code in `pydantic/json_schema.py`

```python
def __init__(
    self, examples: dict[str, Any] | list[Any], mode: Literal['validation', 'serialization'] | None = None
) -> None:
    if isinstance(examples, dict):
        warnings.warn(
            'Using a dict for `examples` is deprecated, use a list instead.',
            PydanticDeprecatedSince29,
            stacklevel=2,
        )
    self.examples = examples
    self.mode = mode

```

## SkipJsonSchema

```python
SkipJsonSchema()

```

Usage Documentation

[`SkipJsonSchema` Annotation](../../concepts/json_schema/#skipjsonschema-annotation)

Add this as an annotation on a field to skip generating a JSON schema for that field.

Example

```python
from pprint import pprint
from typing import Union

from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema

class Model(BaseModel):
    a: Union[int, None] = None  # (1)!
    b: Union[int, SkipJsonSchema[None]] = None  # (2)!
    c: SkipJsonSchema[Union[int, None]] = None  # (3)!

pprint(Model.model_json_schema())
'''
{
    'properties': {
        'a': {
            'anyOf': [
                {'type': 'integer'},
                {'type': 'null'}
            ],
            'default': None,
            'title': 'A'
        },
        'b': {
            'default': None,
            'title': 'B',
            'type': 'integer'
        }
    },
    'title': 'Model',
    'type': 'object'
}
'''

```

1. The integer and null types are both included in the schema for `a`.
1. The integer type is the only type included in the schema for `b`.
1. The entirety of the `c` field is omitted from the schema.

## model_json_schema

```python
model_json_schema(
    cls: type[BaseModel] | type[PydanticDataclass],
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[
        GenerateJsonSchema
    ] = GenerateJsonSchema,
    mode: JsonSchemaMode = "validation",
) -> dict[str, Any]

```

Utility function to generate a JSON Schema for a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `type[BaseModel] | type[PydanticDataclass]` | The model class to generate a JSON Schema for. | *required* | | `by_alias` | `bool` | If True (the default), fields will be serialized according to their alias. If False, fields will be serialized according to their attribute name. | `True` | | `ref_template` | `str` | The template to use for generating JSON Schema references. | `DEFAULT_REF_TEMPLATE` | | `schema_generator` | `type[GenerateJsonSchema]` | The class to use for generating the JSON Schema. | `GenerateJsonSchema` | | `mode` | `JsonSchemaMode` | The mode to use for generating the JSON Schema. It can be one of the following: 'validation': Generate a JSON Schema for validating data. 'serialization': Generate a JSON Schema for serializing data. | `'validation'` |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | The generated JSON Schema. |

Source code in `pydantic/json_schema.py`

```python
def model_json_schema(
    cls: type[BaseModel] | type[PydanticDataclass],
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    mode: JsonSchemaMode = 'validation',
) -> dict[str, Any]:
    """Utility function to generate a JSON Schema for a model.

    Args:
        cls: The model class to generate a JSON Schema for.
        by_alias: If `True` (the default), fields will be serialized according to their alias.
            If `False`, fields will be serialized according to their attribute name.
        ref_template: The template to use for generating JSON Schema references.
        schema_generator: The class to use for generating the JSON Schema.
        mode: The mode to use for generating the JSON Schema. It can be one of the following:

            - 'validation': Generate a JSON Schema for validating data.
            - 'serialization': Generate a JSON Schema for serializing data.

    Returns:
        The generated JSON Schema.
    """
    from .main import BaseModel

    schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

    if isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema):
        cls.__pydantic_core_schema__.rebuild()

    if cls is BaseModel:
        raise AttributeError('model_json_schema() must be called on a subclass of BaseModel, not BaseModel itself.')

    assert not isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema), 'this is a bug! please report it'
    return schema_generator_instance.generate(cls.__pydantic_core_schema__, mode=mode)

```

## models_json_schema

```python
models_json_schema(
    models: Sequence[
        tuple[
            type[BaseModel] | type[PydanticDataclass],
            JsonSchemaMode,
        ]
    ],
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[
        GenerateJsonSchema
    ] = GenerateJsonSchema
) -> tuple[
    dict[
        tuple[
            type[BaseModel] | type[PydanticDataclass],
            JsonSchemaMode,
        ],
        JsonSchemaValue,
    ],
    JsonSchemaValue,
]

```

Utility function to generate a JSON Schema for multiple models.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `models` | `Sequence[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode]]` | A sequence of tuples of the form (model, mode). | *required* | | `by_alias` | `bool` | Whether field aliases should be used as keys in the generated JSON Schema. | `True` | | `title` | `str | None` | The title of the generated JSON Schema. | `None` | | `description` | `str | None` | The description of the generated JSON Schema. | `None` | | `ref_template` | `str` | The reference template to use for generating JSON Schema references. | `DEFAULT_REF_TEMPLATE` | | `schema_generator` | `type[GenerateJsonSchema]` | The schema generator to use for generating the JSON Schema. | `GenerateJsonSchema` |

Returns:

| Type | Description | | --- | --- | | `tuple[dict[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]` | A tuple where: - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have JsonRef references to definitions that are defined in the second returned element.) - The second element is a JSON schema containing all definitions referenced in the first returned element, along with the optional title and description keys. |

Source code in `pydantic/json_schema.py`

```python
def models_json_schema(
    models: Sequence[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode]],
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> tuple[dict[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
    """Utility function to generate a JSON Schema for multiple models.

    Args:
        models: A sequence of tuples of the form (model, mode).
        by_alias: Whether field aliases should be used as keys in the generated JSON Schema.
        title: The title of the generated JSON Schema.
        description: The description of the generated JSON Schema.
        ref_template: The reference template to use for generating JSON Schema references.
        schema_generator: The schema generator to use for generating the JSON Schema.

    Returns:
        A tuple where:
            - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                JsonRef references to definitions that are defined in the second returned element.)
            - The second element is a JSON schema containing all definitions referenced in the first returned
                    element, along with the optional title and description keys.
    """
    for cls, _ in models:
        if isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema):
            cls.__pydantic_core_schema__.rebuild()

    instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
    inputs: list[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode, CoreSchema]] = [
        (m, mode, m.__pydantic_core_schema__) for m, mode in models
    ]
    json_schemas_map, definitions = instance.generate_definitions(inputs)

    json_schema: dict[str, Any] = {}
    if definitions:
        json_schema['$defs'] = definitions
    if title:
        json_schema['title'] = title
    if description:
        json_schema['description'] = description

    return json_schemas_map, json_schema

```
