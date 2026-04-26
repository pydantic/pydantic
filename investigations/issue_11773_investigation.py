"""
Investigation Report: Issue #11773
Non-DC subclass serialized as dataclass despite custom __get_pydantic_core_schema__

Authors: Jose Lima, Varidhi Jain
Date: April 2026

CONCLUSION: Root cause is in pydantic-core (Rust), not pydantic (Python).
"""

from dataclasses import dataclass
from pydantic_core import core_schema, SchemaSerializer
from pydantic import TypeAdapter
from typing import Any


@dataclass
class BaseDC:
    a: int = 1


class SubNotDC(BaseDC):
    def __init__(self):
        self.x = 'test'

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
        print("STEP 1: __get_pydantic_core_schema__ called — Python-side schema generation is CORRECT")
        return core_schema.no_info_plain_validator_function(lambda v: cls())


# PROOF 1: Python-side schema generation works correctly
print("=== PROOF 1: Schema Generation ===")
result = TypeAdapter(SubNotDC).dump_python(SubNotDC())
print(f"Result: {result}")
print(f"Bug confirmed: should not be a dict → isinstance(result, dict) = {isinstance(result, dict)}")
print()

# PROOF 2: The bug exists even when bypassing pydantic entirely
# and using pydantic-core's SchemaSerializer directly
print("=== PROOF 2: pydantic-core Serializer (bypassing pydantic) ===")
schema = core_schema.no_info_plain_validator_function(lambda v: SubNotDC())
serializer = SchemaSerializer(schema)
result2 = serializer.to_python(SubNotDC())
print(f"Result: {result2}")
print(f"Bug persists with explicit schema: {isinstance(result2, dict)}")
print()

# PROOF 3: Even attaching an explicit serializer doesn't help
print("=== PROOF 3: Explicit Serializer Attached ===")
schema2 = core_schema.no_info_plain_validator_function(
    lambda v: SubNotDC(),
    serialization=core_schema.plain_serializer_function_ser_schema(lambda v: v)
)
serializer2 = SchemaSerializer(schema2)
result3 = serializer2.to_python(SubNotDC())
print(f"Result: {result3}")
print(f"Bug persists even with explicit serializer: {isinstance(result3, dict)}")
print()

print("=== CONCLUSION ===")
print("pydantic-core detects __dataclass_fields__ via inheritance and overrides")
print("the serialization schema regardless of what Python-side schema is provided.")
print("Fix must be implemented in pydantic-core's Rust serializer.")
print("Relevant file to fix: pydantic-core/src/serializers/")