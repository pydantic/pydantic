from pydantic.json_schema import Examples

e_good = Examples([])
e_deprecated = Examples({})  # pyright: ignore[reportDeprecated]
