The following table provides details on how Pydantic converts data during validation in both strict and lax modes.

"Lax mode" indicates the default behavior of Pydantic, where it attempts to coerce values to the correct type, when possible. "Strict mode" indicates the behavior of Pydantic when `strict=True` is set on either a field or on a model config.

See [Strict Mode](models.md#strict-mode) for more details.

=== "All"
{{ conversion_table_all }}

=== "JSON"
{{ conversion_table_json }}

=== "JSON - Strict"
{{ conversion_table_json_strict }}

=== "Python"
{{ conversion_table_python }}

=== "Python - Strict"
{{ conversion_table_python_strict }}
