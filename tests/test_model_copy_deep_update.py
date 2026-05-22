"""
Tests for pydantic/pydantic issue #13077
`model_copy(deep=True, update=...)` unnecessarily deepcopies fields
that will be replaced by `update`.

To run:  pytest tests/test_model_copy_deep_update.py -v
"""

import pytest
from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class _NonCopyable:
    """Simulates a native/external object that raises on deepcopy (e.g. GPU tensor, file handle)."""

    def __deepcopy__(self, memo):
        raise TypeError("This object cannot be deepcopied")


class _Trackable:
    """Records how many times it was deepcopied so we can assert skipped copies."""

    copy_count = 0

    def __deepcopy__(self, memo):
        _Trackable.copy_count += 1
        clone = _Trackable()
        memo[id(self)] = clone
        return clone


# ─────────────────────────────────────────────────────────────────────────────
# Models under test
# ─────────────────────────────────────────────────────────────────────────────

class SimpleModel(BaseModel):
    name: str
    value: int


class ArbitraryModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    engine: object = None


class ExtraModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestModelCopyDeepUpdate:

    # ── Regression: non-copyable field is replaced via update ────────────────

    def test_non_copyable_field_replaced_in_update_does_not_raise(self):
        """
        When the user explicitly replaces a non-copyable field via `update`,
        model_copy(deep=True) must NOT attempt to deepcopy it.
        Before the fix this raised TypeError.
        """
        nc = _NonCopyable()
        m = ArbitraryModel(name="original", engine=nc)

        # Should not raise even though `engine` cannot be deepcopied,
        # because we are replacing it.
        copy = m.model_copy(deep=True, update={"engine": None})

        assert copy.engine is None
        assert copy.name == "original"          # other fields still copied
        assert copy.name is not m.name          # ... and deepcopied (new str object)

    # ── Performance: updated fields are NOT deepcopied ────────────────────────

    def test_updated_fields_are_skipped_during_deepcopy(self):
        """Fields in `update` must not incur a deepcopy call."""
        _Trackable.copy_count = 0
        t = _Trackable()
        m = ArbitraryModel(name="x", engine=t)

        # Replace the trackable → it should NOT be deepcopied.
        _ = m.model_copy(deep=True, update={"engine": "replaced"})

        assert _Trackable.copy_count == 0, (
            f"engine was deepcopied {_Trackable.copy_count} time(s) even though it is in `update`"
        )

    def test_non_updated_fields_are_still_deepcopied(self):
        """Fields NOT in `update` must still be deepcopied."""
        inner = [1, 2, 3]
        m = SimpleModel(name="hello", value=42)

        # Patch __dict__ to insert a mutable list so we can check identity.
        m.__dict__["_extra_list"] = inner  # type: ignore[assignment]

        copy = m.model_copy(deep=True, update={"value": 99})

        assert copy.__dict__.get("_extra_list") is not inner  # deepcopied → new object
        assert copy.__dict__.get("_extra_list") == inner       # but same content

    # ── Correctness: update values are applied ────────────────────────────────

    def test_update_values_are_present_on_copy(self):
        m = SimpleModel(name="alice", value=1)
        copy = m.model_copy(deep=True, update={"name": "bob", "value": 2})

        assert copy.name == "bob"
        assert copy.value == 2

    def test_original_is_not_mutated(self):
        m = SimpleModel(name="alice", value=1)
        _ = m.model_copy(deep=True, update={"name": "bob"})

        assert m.name == "alice"   # original untouched

    # ── Shared references preserved via memo ─────────────────────────────────

    def test_shared_references_preserved_across_fields(self):
        """
        If two fields reference the same object, the deepcopied model should
        preserve that shared identity (not create two independent copies).
        """
        shared = [42]

        class SharedModel(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            a: object
            b: object

        m = SharedModel(a=shared, b=shared)
        assert m.a is m.b  # sanity: they share the same list

        copy = m.model_copy(deep=True, update={})  # empty update → full deep branch

        assert copy.a is copy.b, "Shared reference should be preserved after deepcopy"
        assert copy.a is not shared  # but it's a new object

    # ── Extra fields (extra="allow") ─────────────────────────────────────────

    def test_extra_field_replaced_via_update_not_deepcopied(self):
        nc = _NonCopyable()
        m = ExtraModel(name="test")
        m.__pydantic_extra__ = {"dynamic": nc}  # type: ignore[assignment]

        # Replacing the extra field must not raise.
        copy = m.model_copy(deep=True, update={"dynamic": "safe_value"})

        assert copy.__pydantic_extra__ is not None
        assert copy.__pydantic_extra__["dynamic"] == "safe_value"

    # ── Backward-compatible paths ─────────────────────────────────────────────

    def test_deep_without_update_still_works(self):
        m = SimpleModel(name="hello", value=7)
        copy = m.model_copy(deep=True)

        assert copy == m
        assert copy is not m

    def test_shallow_copy_without_update_still_works(self):
        m = SimpleModel(name="hello", value=7)
        copy = m.model_copy()

        assert copy == m
        assert copy is not m

    def test_shallow_copy_with_update_still_works(self):
        m = SimpleModel(name="hello", value=7)
        copy = m.model_copy(update={"name": "world"})

        assert copy.name == "world"
        assert copy.value == 7

    # ── pydantic_fields_set updated correctly ─────────────────────────────────

    def test_fields_set_updated_after_copy(self):
        m = SimpleModel(name="alice", value=1)
        copy = m.model_copy(deep=True, update={"value": 99})

        assert "value" in copy.model_fields_set
