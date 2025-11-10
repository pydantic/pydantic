"""Experimental `struct` type, for lightweight data structures using Pydantic validation."""

from typing import dataclass_transform

from pydantic_core._structs import create_struct_type

from ..dataclasses import dataclass
from ..fields import Field

# TODO this is a basic skeleton implementation, to be replaced with a real one
# after the code structure is in place.


@dataclass_transform(field_specifiers=(Field,))
def struct(cls: type | None = None, *args, **kwargs):
    """Define a `struct` with Pydantic validation."""
    # NB, this is currently implemented as a decorator, but it may be more appropriate
    # to use a metaclass, as this decorator doesn't modify the class in-place but rather
    # creates a new one.
    #
    # However that does run the risk of metaclass conflicts. BaseModel already has this
    # problem and the metaclass inherits from ABCMeta, so we could repeat that pattern
    # here.

    def wrapper(cls):
        # TODO: resolve core schema of struct type in Python, give the core schema to Rust,
        # don't actually use the dataclass decorator at all.
        return create_struct_type(dataclass(cls, *args, **kwargs))

    if cls is not None:
        return wrapper(cls)

    return wrapper
