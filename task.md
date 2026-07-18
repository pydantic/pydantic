## Initial failing state

`BaseModel.model_validate(..., aggregate_errors=True)` is rejected because the
runtime option does not exist.

## Target behavior

Expose `aggregate_errors` on the documented validation entry points and pass it
to pydantic-core as per-call state. When it is true, constrained strings
aggregate only simultaneous `min_length` and `pattern` failures. When omitted
or false, observable validation behavior is unchanged.

### Scope

Current implementation scope

When `aggregate_errors=True`, constrained string validation aggregates only
`min_length` and `pattern` failures evaluated for the same transformed string
value. `ascii_only`, `max_length`, type conversion, and all other constraint
families preserve their existing behavior. `strip_whitespace` retains its
existing pre-constraint transform behavior; `to_lower` and `to_upper` retain
their existing post-validation transform behavior. This is intentionally not a
general exhaustive-validation framework.

- Public methods accepting `aggregate_errors`: `model_validate`, `model_validate_json`, `model_validate_strings`, `TypeAdapter.validate_python`, `validate_json`, `validate_strings`
- Aggregated constraints: `min_length`, `pattern` only
- Explicit exclusions: `max_length`, `ascii_only`, `strip_whitespace` (pre-constraint transform, not aggregated), `to_lower`/`to_upper` (post-validation transforms, not aggregated), all non-string validators, type-level failures (`string_type` always terminal)
- Default compatibility: `omitted` and `aggregate_errors=False` produce identical output
- Plugin compatibility: no plugin protocol signature changes; `aggregate_errors` filtered at `_schema_validator.py` wrapper before third-party callbacks

## Out of scope

This benchmark does not require a general exhaustive-validation framework.

Excluded behavior includes:
- `max_length` aggregation
- Numeric, bytes, collection, date/time, and other non-string constraints
- Custom field-validator aggregation
- Model-validator aggregation
- Union branch-policy changes
- Constructor, assignment-validation, settings, and serialization changes

Only constrained-string `min_length` and `pattern` failures are aggregated
when `aggregate_errors=True`.

- [x] Verification: Confirm aggregate_errors is accepted but existing validation behavior is unchanged (1 error returned, regression suite passes).
- [x] Phase 2: String Validation Surgical Slice (Rust)
- [x] Add aggregate_errors fallback path in StrConstrainedValidator::validate
- [x] Ensure parity across JSON schema paths
- [x] Refactor to Vec<ValLineError> aggregation
- [x] RC1 Verification
- [x] Plugin Signature Filtering Option A in wrapper
- [x] RC2.5 Final Gate Check
- [x] RC3 Final Gate (Documentation cleanup and clippy verification)
