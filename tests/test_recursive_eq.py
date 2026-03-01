from typing import Optional

from pydantic import BaseModel


def test_recursive_model_equality():
    """Test that comparing models with self-references doesn't cause infinite recursion."""

    class RecursiveModel(BaseModel):
        value: int
        parent: Optional['RecursiveModel'] = None

    # Create a model with a reference to itself
    model = RecursiveModel(value=1)
    model.parent = model

    # This should not cause infinite recursion
    assert model == model

    # Create another model with the same structure
    model2 = RecursiveModel(value=1)
    model2.parent = model2

    # These models should be equal
    assert model == model2

    # Create a model with a different value
    model3 = RecursiveModel(value=2)
    model3.parent = model3

    # These models should not be equal
    assert model != model3


def test_recursive_model_complex_cycle():
    """Test that comparing models with complex reference cycles doesn't cause infinite recursion."""

    class Node(BaseModel):
        value: int
        children: list['Node'] = []

    # Create a cycle: root -> child1 -> child2 -> root
    root = Node(value=1)
    child1 = Node(value=2)
    child2 = Node(value=3)

    root.children = [child1]
    child1.children = [child2]
    child2.children = [root]

    # This should not cause infinite recursion
    assert root == root

    # Create another identical structure
    root2 = Node(value=1)
    child1_2 = Node(value=2)
    child2_2 = Node(value=3)

    root2.children = [child1_2]
    child1_2.children = [child2_2]
    child2_2.children = [root2]

    # These should be equal
    assert root == root2

    # Create a structure with a different value
    root3 = Node(value=4)
    child1_3 = Node(value=2)
    child2_3 = Node(value=3)

    root3.children = [child1_3]
    child1_3.children = [child2_3]
    child2_3.children = [root3]

    # These should not be equal
    assert root != root3
