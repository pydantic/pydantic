"""The type handlers for the types supported by Pydantic.

Importing this package registers the type handlers in the default registry. The import order matters,
as predicates are checked in registration order.
"""

# Pydantic models are the most common referenced types, so their type handler is registered first:
from . import _models, _typing, _builtins, _collections, _stdlib  # noqa: F401  # isort: skip
