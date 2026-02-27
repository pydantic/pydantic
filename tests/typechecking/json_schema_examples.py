from pydantic.json_schema import Examples

e_good = Examples([])
e_deprecated = Examples({})  # type: ignore[deprecated]  # pyright: ignore[reportDeprecated]
