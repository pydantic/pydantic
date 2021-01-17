Add support for `NamedTuple` and `TypedDict` types.
Those two types are now handled and validated when used inside `BaseModel` or _pydantic_ `dataclass`.
Two utils are also added `create_model_from_namedtuple` and `create_model_from_typeddict`.