The following table provides details on how Pydantic converts data during validation in both strict and lax modes.

"Lax mode" indicates the default behavior of Pydantic, where it attempts to coerce values to the correct type, when possible. "Strict mode" indicates the behavior of Pydantic when `strict=True` is set on either a field or `strict=True` is set on a model config.

See [Strict Mode](strict_mode.md) for more details.

{{ conversion_table }}
