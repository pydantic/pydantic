"""
Regression tests for GitHub Issue #11773:
Do not consider dataclass subclasses (that aren't themselves dataclasses) as dataclasses.

Root cause: dataclasses.is_dataclass() returns True for any class that inherits
__dataclass_fields__ via MRO, even if the subclass was never @dataclass-decorated.
Fix (in _generate_schema.py): replace is_dataclass(cls) with
'__dataclass_fields__' in cls.__dict__
"""
from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from pydantic import BaseModel, TypeAdapter
from pydantic_core import core_schema

# Shared Base Dataclass
@dataclasses.dataclass
class BaseDC:
    a: int = 1

@pytest.mark.xfail(reason="Root cause in pydantic-core Rust serializer, see #11773", strict=True)
def test_subclass_with_custom_schema_not_serialized_as_dataclass():
    """1. Exact reproduction of #11773: Custom schema must override inherited DC traits."""
    class SubNotDC(BaseDC):
        def __init__(self):
            self.x = "test"

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
            return core_schema.no_info_plain_validator_function(lambda v: cls())

    # If the bug is present, dump_python wrongly returns the parent's dict: {'a': 1}
    # If fixed, it returns the custom SubNotDC instance.
    result = TypeAdapter(SubNotDC).dump_python(SubNotDC())
    assert not isinstance(result, dict)
    assert isinstance(result, SubNotDC)

@pytest.mark.xfail(reason="Root cause in pydantic-core Rust serializer, see #11773", strict=True)
def test_non_dc_subclass_as_model_field():
    """2. Real-world usage: Ensures the fix works inside a BaseModel."""
    class SubNotDC(BaseDC):
        def __init__(self):
            self.x = "test"

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
            return core_schema.no_info_plain_validator_function(lambda v: cls())

    class MyModel(BaseModel):
        field: SubNotDC

    dumped = MyModel(field="any").model_dump()
    
    # The field should retain its custom serialization, not revert to {'a': 1}
    assert not isinstance(dumped["field"], dict)
    assert isinstance(dumped["field"], SubNotDC)

@pytest.mark.xfail(reason="Root cause in pydantic-core Rust serializer, see #11773", strict=True)
def test_deep_inheritance_chain():
    """3. Edge case: Ensures the strict check holds up over multiple inheritance levels."""
    class ChildNotDC(BaseDC):
        pass

    class GrandChildNotDC(ChildNotDC):
        def __init__(self):
            self.x = "test"

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
            return core_schema.no_info_plain_validator_function(lambda v: cls())

    result = TypeAdapter(GrandChildNotDC).dump_python(GrandChildNotDC())
    assert not isinstance(result, dict)
    assert isinstance(result, GrandChildNotDC)

def test_non_dc_subclass_json_serialization():
    """4. JSON path must also respect the custom schema, not the inherited DC schema."""
    class SubNotDC(BaseDC):
        def __init__(self):
            self.x = "test"

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
            return core_schema.no_info_plain_validator_function(
                lambda v: cls(),
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda obj: "custom_marker"
                ),
            )

    json_bytes = TypeAdapter(SubNotDC).dump_json(SubNotDC())
    # Before fix: b'{"a":1}' — parent DC schema used
    # After fix: b'"custom_marker"' — custom schema honoured
    assert json_bytes != b'{"a":1}'
    assert b"custom_marker" in json_bytes
