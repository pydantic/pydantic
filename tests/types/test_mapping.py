from collections import UserDict
from collections.abc import Mapping, MutableMapping
from typing import Any

import pytest

from pydantic import ConfigDict, PydanticSchemaGenerationError, TypeAdapter, ValidationError


def test_mapping_subclass_without_core_schema() -> None:
    class MyDict(dict[int, int]):
        # The point of this is that subclasses can do arbitrary things
        # This is the reason why we don't try to handle them automatically
        # TBD if we introspect `__init__` / `__new__`
        # (which is the main thing that would mess us up if modified in a subclass)
        # and automatically handle cases where the subclass doesn't override it.
        # There's still edge cases (again, arbitrary behavior...)
        # and it's harder to explain, but could lead to a better user experience in some cases
        # It will depend on how the complaints (which have and will happen in both directions)
        # balance out
        def __init__(self, *args: Any, required: int, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)

    with pytest.raises(
        PydanticSchemaGenerationError, match='implement `__get_pydantic_core_schema__` on your type to fully support it'
    ):
        TypeAdapter(MyDict)


def test_mutable_mapping_userdict_subclass() -> None:
    """Addresses https://github.com/pydantic/pydantic/issues/9549.

    Note - we still don't do a good job of handling subclasses, as we convert the input to a dict.
    """
    adapter = TypeAdapter(MutableMapping, config=ConfigDict(strict=True))

    assert isinstance(adapter.validate_python(UserDict()), MutableMapping)


def test_mapping_parameterized() -> None:
    """https://github.com/pydantic/pydantic/issues/11650"""
    adapter = TypeAdapter(Mapping[str, int])

    with pytest.raises(ValidationError):
        adapter.validate_python({'valid': 1, 'invalid': {}})
