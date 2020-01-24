**Breaking Change:** alias precedence logic changed so aliases on a field always take priority over
an alias from `alias_generator` to avoid buggy/unexpected behaviour,
see [here](https://pydantic-docs.helpmanual.io/usage/model_config/#alias-precedence) for details
