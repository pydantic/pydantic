from typing import Any

from typing_extensions import assert_type

from pydantic import ImportString
from pydantic.json_schema import Examples

e_good = Examples([])
e_deprecated = Examples({})  # pyright: ignore[reportDeprecated]

# `ImportString` is defined as `Annotated[AnyType, ...]` (`AnyType` is a type var).
# If not parametrized, type checkers will complain provided they are configured
# to do so on missing type arguments (for pyright, this is controlled
# by `reportMissingTypeArgument`). This shouldn't error because we use
# a default value for the type var.
i_any: ImportString = ...

assert_type(i_any, ImportString[Any])
