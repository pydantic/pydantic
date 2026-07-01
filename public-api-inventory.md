# Pydantic public API inventory

This document inventories **public** API surface for **Pydantic V2** as shipped in this repository (package version per `pydantic/version.py`, core pinned via `pydantic-core`). “Public” means symbols users and integrators are expected to import from `pydantic`, documented submodules (`pydantic.dataclasses`, `pydantic.json_schema`, `pydantic.alias_generators`, `pydantic.plugin`, `pydantic.experimental`, `pydantic.deprecated`, `pydantic.v1`, `pydantic.mypy` entry point), or that appear in `pydantic.__all__`.

**Not public** (unless noted as accidental/escape hatches): `pydantic._internal.*`, names starting with `_` that are not part of documented dunder contracts on models, and importing `GenerateSchema` / `FieldValidationInfo` from `pydantic` (deprecated dynamic imports that warn).

Stability legend used below:

| Tag | Meaning |
| --- | ------- |
| **Stable** | Supported public API; changes follow versioning / deprecation policy |
| **Stable-deprecated** | Still importable; emits deprecation; likely removed or relocated in V3 |
| **Provisional** | Documented but may change without the same guarantees (`experimental`) |
| **Extension** | Intended for advanced customization; stable enough to build on, tied to core-schema evolution |
| **Integrators** | For plugins, mypy, frameworks—not typical app models |
| **Compat** | V1 or migration only |
| **Re-export (core)** | Defined in `pydantic-core`; pydantic re-exports for convenience |

For each symbol: **Users**, **Implementation**, **Internal deps**, **Stability**, **Breakage impact**.

---

## 1. Package entry and version

### `pydantic` package (`pydantic/__init__.py`)

Lazy exports via `_dynamic_imports` and `__getattr__`; runs `_ensure_pydantic_core_version()` on import.

### `VERSION` / `__version__`

| | |
| --- | --- |
| **Users** | Packaging, diagnostics, support tickets |
| **Implementation** | `pydantic/version.py` (`VERSION`); `__version__` alias in `__init__.py` |
| **Internal deps** | None (string constant); import checks `pydantic_core.__version__` |
| **Stability** | Stable |
| **Breakage** | Pinning and ecosystem version gates |

### `version_info()`

| | |
| --- | --- |
| **Users** | Debugging environment / related packages |
| **Implementation** | `pydantic/version.py` |
| **Internal deps** | `importlib.metadata`, `pydantic_core`, optional `_internal._git` |
| **Stability** | Stable (output format may gain lines) |
| **Breakage** | Support tooling parsing the string |

---

## 2. Models and dynamic model creation

### `BaseModel`

| | |
| --- | --- |
| **Users** | Primary application and library authors defining data models |
| **Implementation** | `pydantic/main.py`; metaclass `ModelMetaclass` in `_internal/_model_construction.py` |
| **Internal deps** | `_model_construction`, `_generate_schema`, `_fields`, `_decorators`, `_config`, `_generics`, `_mock_val_ser`, plugin `create_schema_validator`, `pydantic_core` (`SchemaValidator` / `SchemaSerializer` / `ValidationError`), `fields`, `json_schema`, `config` |
| **Stability** | **Stable** (core product API) |
| **Breakage** | Nearly all pydantic users; FastAPI/SQLModel/etc.; any change to constructor validation, `model_validate*`, `model_dump*`, `model_json_schema`, `model_config`, `model_fields`, config interplay, or pydantic dunders (`__pydantic_validator__`, etc.) |

**Public methods / attributes (representative; all part of Stable model contract):**  
`model_config`, `model_fields`, `model_computed_fields`, `model_extra`, `model_fields_set`, `__init__`, `model_validate`, `model_validate_json`, `model_validate_strings`, `model_construct`, `model_dump`, `model_dump_json`, `model_copy`, `model_json_schema`, `model_parametrized_name`, `model_rebuild`, `model_post_init` (hook), classmethods for schema/rebuild, equality/hash/repr behavior under config, deprecated V1-style methods still present with warnings (`dict`, `json`, `parse_obj`, `copy`, `schema`, … via deprecated paths).

Changing validation/serialization semantics of these methods without deprecation **breaks** every dependent model and OpenAPI stack relying on dump/schema shapes.

### `create_model`

| | |
| --- | --- |
| **Users** | Dynamic APIs, metaprogramming, frameworks generating models at runtime |
| **Implementation** | `pydantic/main.py` |
| **Internal deps** | Same completion path as `BaseModel` (`complete_model_class` / field definitions) |
| **Stability** | Stable |
| **Breakage** | Dynamic schema builders, some admin/ORM helpers |

### `RootModel`

| | |
| --- | --- |
| **Users** | Models with a single validated “root” value (custom root types, root JSON arrays/objects) |
| **Implementation** | `pydantic/root_model.py` |
| **Internal deps** | `BaseModel`, `_model_construction` metaclass variant |
| **Stability** | Stable |
| **Breakage** | APIs using root models; forbids `extra` config—semantic changes to `root` field handling |

---

## 3. Configuration

### `ConfigDict`

| | |
| --- | --- |
| **Users** | Everyone configuring models, dataclasses, some adapters |
| **Implementation** | `pydantic/config.py` (`TypedDict`) |
| **Internal deps** | Consumed by `_config.ConfigWrapper` → core `CoreConfig` / schema nodes |
| **Stability** | Stable (keys evolve with deprecations, e.g. `populate_by_name` vs `validate_by_name`) |
| **Breakage** | Silent behavior changes (extra, strict, aliases, ser formats) across all models |

### `with_config`

| | |
| --- | --- |
| **Users** | Attaching config to TypedDicts / types that are not `BaseModel` subclasses |
| **Implementation** | `pydantic/config.py` |
| **Internal deps** | Config storage read during schema generation |
| **Stability** | Stable |
| **Breakage** | TypedDict / adapter config discovery |

### `BaseConfig`, `Extra` (deprecated)

| | |
| --- | --- |
| **Users** | Legacy V1-style class-based config |
| **Implementation** | `pydantic/deprecated/config.py` |
| **Internal deps** | `_config` compatibility |
| **Stability** | **Stable-deprecated** |
| **Breakage** | Old codebases; removal in V3 |

---

## 4. Fields, private attributes, computed fields

### `Field` (function)

| | |
| --- | --- |
| **Users** | Declaring field constraints, aliases, defaults, metadata |
| **Implementation** | `pydantic/fields.py` → builds `FieldInfo` |
| **Internal deps** | `_fields`, `aliases`, `annotated_types`, `typing_inspection`, core `PydanticUndefined` / `MISSING` |
| **Stability** | Stable (parameters deprecated over time: `min_items`, `unique_items`, `extra` kwargs, …) |
| **Breakage** | Model field semantics, OpenAPI, validation constraints, FastAPI `Field` subclasses (merge HACKs) |

### `FieldInfo`

| | |
| --- | --- |
| **Users** | Advanced users, framework authors inspecting/modifying fields; not always needed in app code |
| **Implementation** | `pydantic/fields.py` |
| **Internal deps** | Same as fields stack; collected into `model_fields` by `_fields` |
| **Stability** | Stable **as a documented type**, but many attributes are semi-internal; subclassing is used by FastAPI and is sensitive |
| **Breakage** | Attribute renames, merge behavior, metadata list layout |

### `PrivateAttr` / private attribute mechanism

| | |
| --- | --- |
| **Users** | Instance state not part of the model schema |
| **Implementation** | `pydantic/fields.py`; wiring in `_model_construction` |
| **Internal deps** | Metaclass private attr slots / `__pydantic_private__` |
| **Stability** | Stable |
| **Breakage** | Libraries storing non-validated state on models |

### `computed_field` (decorator)

| | |
| --- | --- |
| **Users** | Derived properties included in serialization / JSON schema |
| **Implementation** | `pydantic/fields.py` (`ComputedFieldInfo`) |
| **Internal deps** | Decorator collection; core serializer computed-fields support |
| **Stability** | Stable |
| **Breakage** | API responses relying on computed fields in dumps/schema |

---

## 5. Aliases

### `AliasPath`, `AliasChoices`, `AliasGenerator`

| | |
| --- | --- |
| **Users** | Complex input key paths, multi-alias validation, naming policies |
| **Implementation** | `pydantic/aliases.py` |
| **Internal deps** | Core lookup keys; `_fields` / config `alias_generator` |
| **Stability** | Stable |
| **Breakage** | Population by alias/name, serialization by alias, OpenAPI names |

### `pydantic.alias_generators`: `to_pascal`, `to_camel`, `to_snake`

| | |
| --- | --- |
| **Users** | `AliasGenerator` / config `alias_generator` helpers |
| **Implementation** | `pydantic/alias_generators.py` |
| **Internal deps** | stdlib `re` only |
| **Stability** | Stable |
| **Breakage** | Wire format naming if algorithm changes |

---

## 6. Functional validators

### Decorators: `field_validator`, `model_validator`

| | |
| --- | --- |
| **Users** | Custom validation logic on models/dataclasses |
| **Implementation** | `pydantic/functional_validators.py` |
| **Internal deps** | `_decorators` → embedded as core `function-*` schema nodes; executed by `pydantic-core` calling back into Python |
| **Stability** | Stable |
| **Breakage** | All custom validation; mode/`check_fields` semantics; ordering relative to field validators |

### Annotated-style: `AfterValidator`, `BeforeValidator`, `PlainValidator`, `WrapValidator`

| | |
| --- | --- |
| **Users** | Reusable validation in `Annotated` metadata; shared across models/adapters |
| **Implementation** | `pydantic/functional_validators.py` (`__get_pydantic_core_schema__`) |
| **Internal deps** | Handler pattern; `_generate_schema` |
| **Stability** | Stable |
| **Breakage** | TypeAdapter and model fields using Annotated validators |

### `SkipValidation`, `InstanceOf`, `ValidateAs`

| | |
| --- | --- |
| **Users** | Opt out of validation; isinstance checks; validate-as-type patterns |
| **Implementation** | `pydantic/functional_validators.py` |
| **Internal deps** | Core schema nodes / `GenerateSchema` |
| **Stability** | Stable |
| **Breakage** | Performance-sensitive “trust input” paths; polymorphic helpers |

### `ModelWrapValidatorHandler` (and related Protocol typedefs in module)

| | |
| --- | --- |
| **Users** | Typing wrap model validators |
| **Implementation** | `pydantic/functional_validators.py` |
| **Internal deps** | `pydantic_core` wrap handler types |
| **Stability** | Stable (typing aids) |
| **Breakage** | Type checkers / annotated validator signatures |

### Deprecated: `validator`, `root_validator`

| | |
| --- | --- |
| **Users** | V1-era code |
| **Implementation** | `pydantic/deprecated/class_validators.py` |
| **Internal deps** | `_decorators`, `_decorators_v1` adapters to core |
| **Stability** | **Stable-deprecated** |
| **Breakage** | Large legacy codebases until migration |

---

## 7. Functional serializers

### Decorators: `field_serializer`, `model_serializer`

| | |
| --- | --- |
| **Users** | Custom dump/JSON shapes |
| **Implementation** | `pydantic/functional_serializers.py` |
| **Internal deps** | `_decorators` → core serialization function schemas |
| **Stability** | Stable |
| **Breakage** | API wire formats, caches of `model_dump` output |

### `PlainSerializer`, `WrapSerializer`, `SerializeAsAny`

| | |
| --- | --- |
| **Users** | Annotated serializers; polymorphic serialization |
| **Implementation** | `pydantic/functional_serializers.py` |
| **Internal deps** | Core serializers; infer paths for `SerializeAsAny` |
| **Stability** | Stable |
| **Breakage** | JSON/python dump compatibility |

---

## 8. Type adapter and validate_call

### `TypeAdapter`

| | |
| --- | --- |
| **Users** | Validate/serialize/schema for arbitrary types without a model class; tools; partial migration from `parse_obj_as` |
| **Implementation** | `pydantic/type_adapter.py` |
| **Internal deps** | `_generate_schema`, `_config`, `_mock_val_ser`, plugin validator, `json_schema` |
| **Stability** | Stable |
| **Breakage** | Non-model validation entry points ecosystem-wide |

### `validate_call`

| | |
| --- | --- |
| **Users** | Validated function/method parameters and return values |
| **Implementation** | `pydantic/validate_call_decorator.py` + `_internal/_validate_call.py` |
| **Internal deps** | `GenerateSchema` arguments schema, plugin validator, core |
| **Stability** | Stable |
| **Breakage** | Service entrypoints, CLI tools using validated callables |

### Deprecated: `validate_arguments` (`pydantic.deprecated.decorator` / old import paths)

| | |
| --- | --- |
| **Users** | V1 decorator users |
| **Implementation** | `pydantic/deprecated/decorator.py` |
| **Stability** | **Stable-deprecated** |
| **Breakage** | Legacy only |

---

## 9. Dataclasses (`pydantic.dataclasses`)

### `dataclass`, `rebuild_dataclass`

| | |
| --- | --- |
| **Users** | stdlib-dataclass style with validation |
| **Implementation** | `pydantic/dataclasses.py`, completion in `_internal/_dataclasses.py` |
| **Internal deps** | Same schema/validator pipeline as models; `Field` / config |
| **Stability** | Stable |
| **Breakage** | Codebases preferring dataclasses; inheritance edge cases |

Also: `is_pydantic_dataclass` and related helpers used by internals and advanced users (treat as **Stable** when documented in module API).

---

## 10. JSON Schema

### `WithJsonSchema`, `Examples` (module-level public)

| | |
| --- | --- |
| **Users** | Override/enrich JSON Schema via `Annotated` |
| **Implementation** | `pydantic/json_schema.py` |
| **Internal deps** | `GenerateJsonSchema` hooks |
| **Stability** | Stable (`WithJsonSchema` also on package `__all__`) |
| **Breakage** | OpenAPI / client generators |

### `GenerateJsonSchema`, `model_json_schema`, `models_json_schema`

| | |
| --- | --- |
| **Users** | Customizing JSON Schema generation; multi-model schemas |
| **Implementation** | `pydantic/json_schema.py` |
| **Internal deps** | Core schema walk; `_core_utils`, config, refs/defs |
| **Stability** | **Extension / Stable** — subclassing `GenerateJsonSchema` is supported but method set tracks core schema kinds |
| **Breakage** | OpenAPI tools, schema caches, documentation portals |

### `PydanticJsonSchemaWarning` and warning kinds

| | |
| --- | --- |
| **Users** | Integrators filtering schema warnings |
| **Implementation** | `pydantic/json_schema.py` |
| **Stability** | Stable |
| **Breakage** | Warning filters |

**Note:** Prefer `Model.model_json_schema()` / `TypeAdapter.json_schema()` for app code; class `GenerateJsonSchema` is the customization surface.

---

## 11. Extension handlers (custom types)

### `GetCoreSchemaHandler`, `GetJsonSchemaHandler`

| | |
| --- | --- |
| **Users** | Authors of custom types and `Annotated` metadata implementing `__get_pydantic_core_schema__` / `__get_pydantic_json_schema__` |
| **Implementation** | `pydantic/annotated_handlers.py` (protocols/ABC-style); concrete handlers in `_schema_generation_shared.py` |
| **Internal deps** | Called from `GenerateSchema` / `GenerateJsonSchema` |
| **Stability** | **Extension / Stable** |
| **Breakage** | Entire custom type ecosystem; third-party pydantic types packages |

### `GetPydanticSchema`

| | |
| --- | --- |
| **Users** | Concise custom core+json schema hooks without full classes |
| **Implementation** | `pydantic/types.py` |
| **Internal deps** | Handler protocol |
| **Stability** | Stable |
| **Breakage** | Lightweight custom types |

---

## 12. Types (`pydantic.types` / package exports)

Common pattern for constrained/special types: implemented in `pydantic/types.py` with `__get_pydantic_core_schema__` (and often JSON schema hooks), depending on `_fields.PydanticMetadata`, `_validators` / `_known_annotated_metadata`, and `pydantic_core`. **Users:** application models. **Stability:** Stable unless noted. **Breakage:** validation acceptance and JSON Schema for those annotations.

### Constraint helpers (prefer `Annotated` + metadata long-term)

| Symbol | Notes |
| --- | --- |
| `Strict`, `AllowInfNan`, `StringConstraints` | Stable metadata types |
| `conint`, `confloat`, `conbytes`, `constr`, `condecimal`, `condate`, `conlist`, `conset`, `confrozenset` | **Stable-deprecated trajectory** (docs: deprecate in favor of `Annotated` for V3) |
| `PositiveInt`, `NegativeInt`, `NonNegativeInt`, `NonPositiveInt` | Stable aliases |
| `PositiveFloat`, `NegativeFloat`, `NonNegativeFloat`, `NonPositiveFloat`, `FiniteFloat` | Stable aliases |
| `StrictBool`, `StrictBytes`, `StrictInt`, `StrictFloat`, `StrictStr` | Stable |

### Secrets and sensitive data

| Symbol | Implementation notes |
| --- | --- |
| `Secret`, `SecretStr`, `SecretBytes` | Custom ser/repr; core-aware |

### Paths and imports

| Symbol | |
| --- | --- |
| `FilePath`, `DirectoryPath`, `NewPath`, `SocketPath` | Path validation |
| `ImportString` | Import dotted paths (replaces V1 `PyObject`) |

### UUID / temporal / JSON

| Symbol | |
| --- | --- |
| `UUID1`–`UUID8` | Version-constrained UUIDs |
| `PastDate`, `FutureDate`, `PastDatetime`, `FutureDatetime`, `AwareDatetime`, `NaiveDatetime` | Temporal constraints |
| `Json`, `JsonValue` | JSON-carrying / JSON-value types |
| `ByteSize` | Human size strings ↔ int |

### Encoding

| Symbol | |
| --- | --- |
| `EncoderProtocol` | Protocol for codecs |
| `EncodedBytes`, `EncodedStr`, `Base64Encoder`, `Base64Bytes`, `Base64Str`, `Base64UrlBytes`, `Base64UrlStr` | Encoded payloads |

### Unions / discrimination / error behavior

| Symbol | |
| --- | --- |
| `Tag`, `Discriminator` | Discriminated unions (`_discriminated_union` + core tagged union) |
| `OnErrorOmit` | Omit union members on error (also on package `__all__`) |
| `FailFast` | Fail fast validation metadata |

### Deprecated type

| Symbol | |
| --- | --- |
| `PaymentCardNumber` | **Stable-deprecated** → `pydantic_extra_types` |

**Breakage for types generally:** changing coercion rules or JSON Schema for a type breaks stored data assumptions and generated clients.

---

## 13. Networks (`pydantic.networks`)

| Symbol | Users | Implementation | Deps | Stability | Breakage |
| --- | --- | --- | --- | --- | --- |
| `UrlConstraints` | Annotate URL limits | `networks.py` | core URL schemas | Stable | URL acceptance |
| `AnyUrl`, `AnyHttpUrl`, `HttpUrl`, `FileUrl`, `FtpUrl`, `WebsocketUrl`, `AnyWebsocketUrl` | URL fields | `networks.py` + `pydantic_core.Url` | `TypeAdapter` builders, core | Stable | URL parsing/normalization |
| DSN types: `PostgresDsn`, `CockroachDsn`, `AmqpDsn`, `RedisDsn`, `MongoDsn`, `KafkaDsn`, `NatsDsn`, `MySQLDsn`, `MariaDBDsn`, `ClickHouseDsn`, `SnowflakeDsn` | Connection strings | `networks.py` + multi-host URL | core `MultiHostUrl` | Stable | Config validation for infra |
| `EmailStr`, `NameEmail`, `validate_email` | Email fields | `networks.py` | optional `email_validator` | Stable | Email acceptance; extra require `pydantic[email]` |
| `IPvAnyAddress`, `IPvAnyInterface`, `IPvAnyNetwork` | IP types | `networks.py` / typing aliases + validators | `_validators` / core | Stable | IP parsing |

---

## 14. Errors and exceptions

### `ValidationError` (re-export)

| | |
| --- | --- |
| **Users** | Everyone handling failed validation |
| **Implementation** | `pydantic_core` |
| **Internal deps** | Rust error lines/locations |
| **Stability** | **Re-export (core)** — error `type` codes are part of public contract |
| **Breakage** | Error handling, i18n maps, HTTP 422 mappers (FastAPI) |

### `PydanticUserError`

| | |
| --- | --- |
| **Users** | Catch incorrect library usage (not input validation) |
| **Implementation** | `pydantic/errors.py` |
| **Internal deps** | Raised throughout `_internal` / public when misconfigured |
| **Stability** | Stable |
| **Breakage** | Startup/config error handling; `code` strings in `PydanticErrorCodes` |

### `PydanticSchemaGenerationError`

| | |
| --- | --- |
| **Users** | Handling types pydantic cannot build schemas for |
| **Implementation** | `errors.py` |
| **Stability** | Stable |
| **Breakage** | Dynamic model builders |

### `PydanticUndefinedAnnotation`

| | |
| --- | --- |
| **Users** | Forward ref / rebuild flows |
| **Implementation** | `errors.py` |
| **Stability** | Stable |
| **Breakage** | `model_rebuild` UX |

### `PydanticInvalidForJsonSchema`

| | |
| --- | --- |
| **Users** | Schema export failures |
| **Implementation** | `errors.py` |
| **Stability** | Stable |
| **Breakage** | OpenAPI generation error handling |

### `PydanticForbiddenQualifier`

| | |
| --- | --- |
| **Users** | Illegal qualifiers in annotations |
| **Implementation** | `errors.py` |
| **Stability** | Stable |
| **Breakage** | TypedDict/qualifier edge tools |

### `PydanticImportError`

| | |
| --- | --- |
| **Users** | Migration / moved imports |
| **Implementation** | `errors.py` + `_migration` |
| **Stability** | Stable (compat) |
| **Breakage** | Import error messaging |

### `PydanticErrorCodes`

| | |
| --- | --- |
| **Users** | Programmatic handling of user errors |
| **Implementation** | `Literal` union in `errors.py` |
| **Stability** | Stable but **expanding** set |
| **Breakage** | Exhaustive matches on codes |

---

## 15. Warnings

Implemented in `pydantic/warnings.py`.

| Symbol | Users | Stability | Breakage |
| --- | --- | --- | --- |
| `PydanticDeprecationWarning` | Filter deprecations | Stable | Warning filters |
| `PydanticDeprecatedSince20` … `Since212` | Version-specific filters | Stable | Same |
| `PydanticExperimentalWarning` | Experimental features | Stable | Filters |
| `ArbitraryTypeWarning`, `UnsupportedFieldAttributeWarning`, `TypedDictExtraConfigWarning` | Schema generation warnings (`CoreSchemaGenerationWarning` hierarchy) | Stable | CI `-W error` setups |

Not all warning subclasses are on package `__all__`; those in `warnings.__all__` are public when imported from `pydantic.warnings`.

---

## 16. Core re-exports on `pydantic` package

| Symbol | Source | Users | Stability | Breakage |
| --- | --- | --- | --- | --- |
| `ValidationError` | `pydantic_core` | All | Re-export (core) | See errors |
| `ValidationInfo` | `pydantic_core.core_schema` | Validator callables with `info` | Re-export (core) | Validator signatures |
| `SerializationInfo` | core_schema | Serializer callables | Re-export (core) | Serializer signatures |
| `FieldSerializationInfo` | core_schema | Field serializers | Re-export (core) | Same |
| `ValidatorFunctionWrapHandler` | core_schema | Wrap validators | Re-export (core) | Wrap callable typing/runtime |
| `SerializerFunctionWrapHandler` | core_schema | Wrap serializers | Re-export (core) | Same |

Changing these types’ shapes requires **coordinated pydantic-core releases**.

---

## 17. Deprecated tools and JSON/parse helpers

### On package `__all__`: `parse_obj_as`, `schema_of`, `schema_json_of`

| | |
| --- | --- |
| **Users** | V1-style one-off validation / schema |
| **Implementation** | `pydantic/deprecated/tools.py` → `TypeAdapter` / `GenerateJsonSchema` |
| **Stability** | **Stable-deprecated** |
| **Breakage** | Legacy utilities; migrate to `TypeAdapter` |

### `pydantic.deprecated.json`: `pydantic_encoder`, `custom_pydantic_encoder`, `timedelta_isoformat`

| | |
| --- | --- |
| **Users** | Old JSON encoding hooks |
| **Implementation** | `deprecated/json.py` |
| **Stability** | **Stable-deprecated** |
| **Breakage** | Custom JSON dumps still on V1 patterns |

### `pydantic.deprecated.parse`: `load_str_bytes`, `load_file`, `Protocol`

| | |
| --- | --- |
| **Users** | Legacy parse helpers |
| **Stability** | **Stable-deprecated** |

### Deprecated `Color` (`pydantic.color`)

| | |
| --- | --- |
| **Users** | CSS color fields |
| **Implementation** | `pydantic/color.py` |
| **Internal deps** | core schema hooks |
| **Stability** | **Stable-deprecated** → `pydantic_extra_types` |
| **Breakage** | Color parsing in old apps |

---

## 18. Experimental API (`pydantic.experimental`)

Treat as **Provisional**; may emit `PydanticExperimentalWarning` / change freely within policy for experimental modules.

| Symbol | Implementation | Users | Deps | Breakage |
| --- | --- | --- | --- | --- |
| `validate_as`, `validate_as_deferred`, `transform` | `experimental/pipeline.py` | Pipeline-style Annotated constraints | core schema building | Experimental callers only |
| `generate_arguments_schema` | `experimental/arguments_schema.py` | Advanced callable schema | `_generate_schema` | Tooling on experimental path |
| `MISSING` | `experimental/missing_sentinel.py` (re-export core `MISSING`) | Partial / sentinel experiments | `pydantic_core` | Sentinel identity comparisons |

---

## 19. Plugin API (`pydantic.plugin`)

**Integrators** (observability vendors, internal frameworks).

| Symbol | Implementation | Deps | Stability | Breakage |
| --- | --- | --- | --- | --- |
| `PydanticPluginProtocol` | `plugin/__init__.py` | `CoreSchema`, `CoreConfig` | **Extension / Integrators** | All entry-point plugins |
| `BaseValidateHandlerProtocol` | same | — | Extension | Plugin callbacks |
| `ValidatePythonHandlerProtocol` | same | `ValidationError` | Extension | Python validation instrumentation |
| `ValidateJsonHandlerProtocol` | same | | Extension | JSON validation instrumentation |
| `ValidateStringsHandlerProtocol` | same | | Extension | Strings validation instrumentation |
| `SchemaTypePath`, `SchemaKind`, `NewSchemaReturns` | same | | Extension | Plugin registration metadata |

Loader (`plugin/_loader.py`) and `PluggableSchemaValidator` (`plugin/_schema_validator.py`) are **implementation details** of how plugins attach—not imported by app users, but behavior is part of the plugin contract.

**Breakage:** changing `new_schema_validator` signature or when it is invoked breaks Logfire-style integrations.

---

## 20. Mypy plugin

### `pydantic.mypy:plugin` (and supporting classes in `pydantic/mypy.py`)

| | |
| --- | --- |
| **Users** | Type-checker integrators; enabled via mypy config |
| **Implementation** | `pydantic/mypy.py` |
| **Internal deps** | mypy APIs; mirrors model semantics (not runtime `_generate_schema`) |
| **Stability** | **Integrators** — tracks mypy versions; config keys are user-facing |
| **Breakage** | Typed codebases using the plugin; CI typecheck |

Public entry is the **`plugin` function** advertised to mypy. Other classes in the module are effectively plugin internals but historically importable.

---

## 21. V1 compatibility (`pydantic.v1`)

Entire submodule is **Compat** public API for migration: `BaseModel`, `validator`, `Field`, `Schema`, `ValidationError`, `BaseConfig`, etc., implemented under `pydantic/v1/*` as a largely standalone pure-Python stack.

| | |
| --- | --- |
| **Users** | Code not yet on V2; dual-stack apps |
| **Implementation** | `pydantic/v1/` |
| **Internal deps** | Does **not** use `pydantic-core` or modern `_internal` |
| **Stability** | **Compat** — maintained for migration, not new features |
| **Breakage** | Any remaining V1 imports; removing `pydantic.v1` is a major migration event |

Shim modules at `pydantic.utils`, `pydantic.typing`, … redirect through `_migration` (**Compat**).

---

## 22. Documented public submodules (module-as-API)

| Module | Role | Stability |
| --- | --- | --- |
| `pydantic.dataclasses` | Validating dataclasses | Stable |
| `pydantic.json_schema` | JSON Schema generation API | Stable / Extension |
| `pydantic.alias_generators` | Naming helpers | Stable |
| `pydantic.warnings` | Warning types | Stable |
| `pydantic.errors` | User-error types | Stable |
| `pydantic.networks` | Network types | Stable |
| `pydantic.types` | Extra types | Stable |
| `pydantic.fields` | `Field` / `FieldInfo` / … | Stable |
| `pydantic.config` | Config | Stable |
| `pydantic.functional_validators` / `functional_serializers` | Direct imports | Stable |
| `pydantic.plugin` | Plugins | Extension |
| `pydantic.experimental` | Experimental | Provisional |
| `pydantic.deprecated` | Deprecated | Stable-deprecated |
| `pydantic.v1` | V1 | Compat |
| `pydantic.mypy` | mypy plugin | Integrators |
| `pydantic.color` | Color type | Stable-deprecated |

Importing from these modules is supported; **`pydantic._internal` is not**.

---

## 23. Explicitly non-public / unsupported (escape hatches)

| Symbol / area | Why listed | Stability |
| --- | --- | --- |
| `pydantic._internal.*` | Orchestration engine | **Implementation detail** — no semver for internals |
| `GenerateSchema` via `from pydantic import GenerateSchema` | Deprecated dynamic import; warns | **Implementation detail** (use extension hooks instead) |
| `FieldValidationInfo` old name | Renamed to `ValidationInfo` | Deprecated alias |
| Model dunders like `__pydantic_validator__`, `__pydantic_core_schema__` | Required for operation; frameworks may read them | **Semi-public contracts** — treated carefully in docs/internals; changing breaks frameworks |
| `plugin/_loader.py`, `plugin/_schema_validator.py` | Private by naming | Implementation detail |

**Breakage if internals change:** Any code importing `_internal` (including some tests and advanced forks); not considered a breaking change for the public API policy, but painful in practice for power users.

---

## 24. Stability and breakage summary (by blast radius)

1. **Catastrophic if changed without migration path:** `BaseModel` validation/serialization methods, `ValidationError` structure/codes, `Field` / `ConfigDict` core semantics, core schema–driven behavior via `pydantic-core` upgrades.
2. **High:** `TypeAdapter`, `validate_call`, JSON Schema output, alias behavior, discriminated unions (`Discriminator`/`Tag`), plugin protocol.
3. **Medium:** Individual `types.*` / `networks.*` coercion edges, computed fields, serializers/validators ordering.
4. **Low (contained):** `alias_generators` string transforms, `version_info` formatting, experimental pipeline.
5. **Planned removal (V3):** deprecated decorators/tools/config, many `con*` helpers, `Color` / `PaymentCardNumber` in-tree, eventually `pydantic.v1` per version policy.

---

## 25. Cross-reference: `__all__` on `pydantic` package

The following are exported from the top-level package (lazy). Implementation modules are as in `_dynamic_imports` in `pydantic/__init__.py`:

`dataclasses`, `field_validator`, `model_validator`, `AfterValidator`, `BeforeValidator`, `PlainValidator`, `WrapValidator`, `SkipValidation`, `ValidateAs`, `InstanceOf`, `ModelWrapValidatorHandler`, `WithJsonSchema`, `root_validator`, `validator`, `field_serializer`, `model_serializer`, `PlainSerializer`, `SerializeAsAny`, `WrapSerializer`, `ConfigDict`, `with_config`, `BaseConfig`, `Extra`, `validate_call`, `PydanticErrorCodes`, `PydanticUserError`, `PydanticSchemaGenerationError`, `PydanticImportError`, `PydanticUndefinedAnnotation`, `PydanticInvalidForJsonSchema`, `PydanticForbiddenQualifier`, `Field`, `computed_field`, `PrivateAttr`, `AliasChoices`, `AliasGenerator`, `AliasPath`, `BaseModel`, `create_model`, network types and `validate_email`, `RootModel`, `parse_obj_as`, `schema_of`, `schema_json_of`, all listed `types` exports including `OnErrorOmit` / `FailFast`, `TypeAdapter`, `__version__`, `VERSION`, deprecation/experimental warnings listed in `__all__`, `GetCoreSchemaHandler`, `GetJsonSchemaHandler`, `ValidationError`, `ValidationInfo`, `SerializationInfo`, `ValidatorFunctionWrapHandler`, `FieldSerializationInfo`, `SerializerFunctionWrapHandler`.

Additional public API exists **only** on submodules (e.g. `FieldInfo`, `GenerateJsonSchema`, `model_json_schema`, `to_camel`, plugin protocols, experimental symbols, `version_info`, `Color`, full `pydantic.v1`).

---

## 26. Dependency pattern for public symbols (typical)

```text
User import (pydantic / submodule)
  → public module (fields, main, types, …)
    → _internal (schema build, decorators, config wrap)   [not public]
      → pydantic_core (SchemaValidator / SchemaSerializer / ValidationError)
    → optionally plugin wrap on validator construction
```

Extension points (`__get_pydantic_core_schema__`, Annotated validators, plugins) insert user code into that pipeline without importing `_internal` directly.

---

*Generated as an inventory of this repository’s intended public surface. When in doubt, prefer symbols in `pydantic.__all__`, documented modules in the official docs, and avoid `pydantic._internal`.*
