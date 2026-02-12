"""Tests for circular reference handling in BaseModel.__eq__ (GH-10630).

When a BaseModel instance has a self-referencing field (e.g., a.child = a),
calling == should not raise RecursionError. Instead, the recursion guard
should detect the cycle and break it gracefully.
"""

from __future__ import annotations

from pydantic import BaseModel


class Node(BaseModel):
    model_config = {'arbitrary_types_allowed': True}
    value: int = 0
    child: Node | None = None


class TestCircularReferenceEquality:
    """Regression tests for GH-10630: RecursionError in == with circular refs."""

    def test_self_referencing_equal(self):
        """Two self-referencing objects with same values should be equal."""
        a = Node(value=1)
        a.child = a

        b = Node(value=1)
        b.child = b

        assert a == b

    def test_self_referencing_not_equal(self):
        """Two self-referencing objects with different values should not be equal."""
        a = Node(value=1)
        a.child = a

        b = Node(value=2)
        b.child = b

        assert a != b

    def test_same_object_self_ref(self):
        """Comparing a self-referencing object to itself should return True."""
        a = Node(value=1)
        a.child = a

        assert a == a

    def test_mutual_circular_reference(self):
        """Two objects referencing each other should not cause RecursionError."""
        a = Node(value=1)
        b = Node(value=1)
        a.child = b
        b.child = a

        a2 = Node(value=1)
        b2 = Node(value=1)
        a2.child = b2
        b2.child = a2

        assert a == a2

    def test_normal_equality_unaffected(self):
        """Non-circular equality should still work correctly."""
        a = Node(value=1, child=Node(value=2))
        b = Node(value=1, child=Node(value=2))
        c = Node(value=1, child=Node(value=3))

        assert a == b
        assert a != c

    def test_non_basemodel_comparison(self):
        """Comparing BaseModel to non-BaseModel should not raise."""
        a = Node(value=1)
        a.child = a

        assert a != 'not a model'
        assert a != 42
        assert a != None  # noqa: E711

    def test_deep_circular_chain(self):
        """A longer circular chain (a -> b -> c -> a) should not recurse."""
        a = Node(value=1)
        b = Node(value=2)
        c = Node(value=3)
        a.child = b
        b.child = c
        c.child = a

        a2 = Node(value=1)
        b2 = Node(value=2)
        c2 = Node(value=3)
        a2.child = b2
        b2.child = c2
        c2.child = a2

        assert a == a2
