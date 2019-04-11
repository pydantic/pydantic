"""
Tests for python 3.7 behaviour, eg postponed annotations and ForwardRef.
"""
import sys

import pytest

from pydantic import ConfigError, ValidationError

skip_not_37 = pytest.mark.skipif(sys.version_info < (3, 7), reason='testing >= 3.7 behaviour only')


@skip_not_37
def test_postponed_annotations(create_module):
    module = create_module(
        """
from __future__ import annotations
from pydantic import BaseModel

class Model(BaseModel):
    a: int
"""
    )
    m = module.Model(a='123')
    assert m.dict() == {'a': 123}


@skip_not_37
def test_postponed_annotations_optional(create_module):
    module = create_module(
        """
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class Model(BaseModel):
    a: Optional[int]
"""
    )
    assert module.Model(a='123').dict() == {'a': 123}
    assert module.Model().dict() == {'a': None}


@skip_not_37
def test_basic_forward_ref(create_module):
    module = create_module(
        """
from typing import ForwardRef, Optional
from pydantic import BaseModel

class Foo(BaseModel):
    a: int

FooRef = ForwardRef('Foo')

class Bar(BaseModel):
    b: Optional[FooRef]
"""
    )

    assert module.Bar().dict() == {'b': None}
    assert module.Bar(b={'a': '123'}).dict() == {'b': {'a': 123}}


@skip_not_37
def test_self_forward_ref_module(create_module):
    module = create_module(
        """
from typing import ForwardRef
from pydantic import BaseModel

Foo = ForwardRef('Foo')

class Foo(BaseModel):
    a: int = 123
    b: Foo = None

Foo.update_forward_refs()
    """
    )

    assert module.Foo().dict() == {'a': 123, 'b': None}
    assert module.Foo(b={'a': '321'}).dict() == {'a': 123, 'b': {'a': 321, 'b': None}}


@skip_not_37
def test_self_forward_ref_collection(create_module):
    module = create_module(
        """
from typing import ForwardRef, List, Dict
from pydantic import BaseModel

Foo = ForwardRef('Foo')

class Foo(BaseModel):
    a: int = 123
    b: Foo = None
    c: List[Foo] = []
    d: Dict[str, Foo] = {}

Foo.update_forward_refs()
    """
    )

    assert module.Foo().dict() == {'a': 123, 'b': None, 'c': [], 'd': {}}
    assert module.Foo(b={'a': '321'}, c=[{'a': 234}], d={'bar': {'a': 345}}).dict() == {
        'a': 123,
        'b': {'a': 321, 'b': None, 'c': [], 'd': {}},
        'c': [{'a': 234, 'b': None, 'c': [], 'd': {}}],
        'd': {'bar': {'a': 345, 'b': None, 'c': [], 'd': {}}},
    }

    with pytest.raises(ValidationError) as exc_info:
        module.Foo(b={'a': '321'}, c=[{'b': 234}], d={'bar': {'a': 345}})
    assert exc_info.value.errors() == [
        {'loc': ('c', 0, 'b'), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}
    ]


@skip_not_37
def test_self_forward_ref_local(create_module):
    module = create_module(
        """
from typing import ForwardRef
from pydantic import BaseModel

def main():
    Foo = ForwardRef('Foo')

    class Foo(BaseModel):
        a: int = 123
        b: Foo = None

    Foo.update_forward_refs()
    return Foo
    """
    )
    Foo = module.main()
    assert Foo().dict() == {'a': 123, 'b': None}
    assert Foo(b={'a': '321'}).dict() == {'a': 123, 'b': {'a': 321, 'b': None}}


@skip_not_37
def test_missing_update_forward_refs(create_module):
    module = create_module(
        """
from typing import ForwardRef
from pydantic import BaseModel

Foo = ForwardRef('Foo')

class Foo(BaseModel):
    a: int = 123
    b: Foo = None
    """
    )
    with pytest.raises(ConfigError) as exc_info:
        module.Foo(b=123)
    assert str(exc_info.value).startswith('field "b" not yet prepared so type is still a ForwardRef')


@skip_not_37
def test_forward_ref_dataclass(create_module):
    module = create_module(
        """
from __future__ import annotations
from pydantic import UrlStr
from pydantic.dataclasses import dataclass

@dataclass
class Dataclass:
    url: UrlStr
    """
    )
    m = module.Dataclass('http://example.com  ')
    assert m.url == 'http://example.com'


@skip_not_37
def test_forward_ref_sub_types(create_module):
    module = create_module(
        """
from typing import ForwardRef, Union

from pydantic import BaseModel


class Leaf(BaseModel):
    a: str


TreeType = Union[ForwardRef('Node'), Leaf]


class Node(BaseModel):
    value: int
    left: TreeType
    right: TreeType


Node.update_forward_refs()
    """
    )
    Node = module.Node
    Leaf = module.Leaf
    data = {"value": 3, "left": {"a": "foo"}, "right": {"value": 5, "left": {"a": "bar"}, "right": {"a": "buzz"}}}

    node = Node(**data)
    assert isinstance(node.left, Leaf)
    assert isinstance(node.right, Node)


@skip_not_37
def test_forward_ref_nested_sub_types(create_module):
    module = create_module(
        """
from typing import ForwardRef, Tuple, Union

from pydantic import BaseModel


class Leaf(BaseModel):
    a: str


TreeType = Union[Union[Tuple[ForwardRef('Node'), str], int], Leaf]


class Node(BaseModel):
    value: int
    left: TreeType
    right: TreeType


Node.update_forward_refs()
    """
    )
    Node = module.Node
    Leaf = module.Leaf
    data = {
        "value": 3,
        "left": {"a": "foo"},
        "right": [{"value": 5, "left": {"a": "bar"}, "right": {"a": "buzz"}}, "test"],
    }

    node = Node(**data)
    assert isinstance(node.left, Leaf)
    assert isinstance(node.right[0], Node)
