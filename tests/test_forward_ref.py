import sys
from typing import Optional, Tuple

import pytest

from pydantic import BaseModel, ConfigError, ValidationError

skip_pre_37 = pytest.mark.skipif(sys.version_info < (3, 7), reason='testing >= 3.7 behaviour only')

try:
    import future_typing
except ImportError:
    future_typing = None


@skip_pre_37
def test_postponed_annotations(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

class Model(BaseModel):
    a: int
"""
    )
    m = module.Model(a='123')
    assert m.dict() == {'a': 123}


@skip_pre_37
def test_postponed_annotations_optional(create_module):
    module = create_module(
        # language=Python
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


def test_basic_forward_ref(create_module):
    @create_module
    def module():
        from typing import Optional

        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        class Foo(BaseModel):
            a: int

        FooRef = ForwardRef('Foo')

        class Bar(BaseModel):
            b: Optional[FooRef]

    assert module.Bar().dict() == {'b': None}
    assert module.Bar(b={'a': '123'}).dict() == {'b': {'a': 123}}


def test_self_forward_ref_module(create_module):
    @create_module
    def module():
        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        Foo = ForwardRef('Foo')

        class Foo(BaseModel):
            a: int = 123
            b: 'Foo' = None

        Foo.update_forward_refs()

    assert module.Foo().dict() == {'a': 123, 'b': None}
    assert module.Foo(b={'a': '321'}).dict() == {'a': 123, 'b': {'a': 321, 'b': None}}


def test_self_forward_ref_collection(create_module):
    @create_module
    def module():
        from typing import Dict, List

        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        Foo = ForwardRef('Foo')

        class Foo(BaseModel):
            a: int = 123
            b: Foo = None
            c: List[Foo] = []
            d: Dict[str, Foo] = {}

        Foo.update_forward_refs()

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


def test_self_forward_ref_local(create_module):
    @create_module
    def module():
        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        def main():
            Foo = ForwardRef('Foo')

            class Foo(BaseModel):
                a: int = 123
                b: Foo = None

            Foo.update_forward_refs()
            return Foo

    Foo = module.main()
    assert Foo().dict() == {'a': 123, 'b': None}
    assert Foo(b={'a': '321'}).dict() == {'a': 123, 'b': {'a': 321, 'b': None}}


def test_missing_update_forward_refs(create_module):
    @create_module
    def module():
        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        Foo = ForwardRef('Foo')

        class Foo(BaseModel):
            a: int = 123
            b: Foo = None

    with pytest.raises(ConfigError) as exc_info:
        module.Foo(b=123)
    assert str(exc_info.value).startswith('field "b" not yet prepared so type is still a ForwardRef')


def test_forward_ref_dataclass(create_module):
    @create_module
    def module():
        from pydantic import AnyUrl
        from pydantic.dataclasses import dataclass

        @dataclass
        class Dataclass:
            url: AnyUrl

    m = module.Dataclass('http://example.com  ')
    assert m.url == 'http://example.com'


@skip_pre_37
def test_forward_ref_dataclass_with_future_annotations(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import AnyUrl
from pydantic.dataclasses import dataclass

@dataclass
class Dataclass:
    url: AnyUrl
    """
    )
    m = module.Dataclass('http://example.com  ')
    assert m.url == 'http://example.com'


def test_forward_ref_sub_types(create_module):
    @create_module
    def module():
        from typing import Union

        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        class Leaf(BaseModel):
            a: str

        TreeType = Union[ForwardRef('Node'), Leaf]

        class Node(BaseModel):
            value: int
            left: TreeType
            right: TreeType

        Node.update_forward_refs()

    Node = module.Node
    Leaf = module.Leaf
    data = {'value': 3, 'left': {'a': 'foo'}, 'right': {'value': 5, 'left': {'a': 'bar'}, 'right': {'a': 'buzz'}}}

    node = Node(**data)
    assert isinstance(node.left, Leaf)
    assert isinstance(node.right, Node)


def test_forward_ref_nested_sub_types(create_module):
    @create_module
    def module():
        from typing import Tuple, Union

        from pydantic import BaseModel
        from pydantic.typing import ForwardRef

        class Leaf(BaseModel):
            a: str

        TreeType = Union[Union[Tuple[ForwardRef('Node'), str], int], Leaf]

        class Node(BaseModel):
            value: int
            left: TreeType
            right: TreeType

        Node.update_forward_refs()

    Node = module.Node
    Leaf = module.Leaf
    data = {
        'value': 3,
        'left': {'a': 'foo'},
        'right': [{'value': 5, 'left': {'a': 'bar'}, 'right': {'a': 'buzz'}}, 'test'],
    }

    node = Node(**data)
    assert isinstance(node.left, Leaf)
    assert isinstance(node.right[0], Node)


def test_self_reference_json_schema(create_module):
    @create_module
    def module():
        from typing import List

        from pydantic import BaseModel

        class Account(BaseModel):
            name: str
            subaccounts: List['Account'] = []

        Account.update_forward_refs()

    Account = module.Account
    assert Account.schema() == {
        '$ref': '#/definitions/Account',
        'definitions': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/definitions/Account'},
                    },
                },
                'required': ['name'],
            }
        },
    }


@skip_pre_37
def test_self_reference_json_schema_with_future_annotations(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import List
from pydantic import BaseModel

class Account(BaseModel):
  name: str
  subaccounts: List[Account] = []

Account.update_forward_refs()
    """
    )
    Account = module.Account
    assert Account.schema() == {
        '$ref': '#/definitions/Account',
        'definitions': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/definitions/Account'},
                    },
                },
                'required': ['name'],
            }
        },
    }


def test_circular_reference_json_schema(create_module):
    @create_module
    def module():
        from typing import List

        from pydantic import BaseModel

        class Owner(BaseModel):
            account: 'Account'

        class Account(BaseModel):
            name: str
            owner: 'Owner'
            subaccounts: List['Account'] = []

        Account.update_forward_refs()
        Owner.update_forward_refs()

    Account = module.Account
    assert Account.schema() == {
        '$ref': '#/definitions/Account',
        'definitions': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'owner': {'$ref': '#/definitions/Owner'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/definitions/Account'},
                    },
                },
                'required': ['name', 'owner'],
            },
            'Owner': {
                'title': 'Owner',
                'type': 'object',
                'properties': {'account': {'$ref': '#/definitions/Account'}},
                'required': ['account'],
            },
        },
    }


@skip_pre_37
def test_circular_reference_json_schema_with_future_annotations(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import List
from pydantic import BaseModel

class Owner(BaseModel):
  account: Account

class Account(BaseModel):
  name: str
  owner: Owner
  subaccounts: List[Account] = []

Account.update_forward_refs()
Owner.update_forward_refs()
    """
    )
    Account = module.Account
    assert Account.schema() == {
        '$ref': '#/definitions/Account',
        'definitions': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'owner': {'$ref': '#/definitions/Owner'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/definitions/Account'},
                    },
                },
                'required': ['name', 'owner'],
            },
            'Owner': {
                'title': 'Owner',
                'type': 'object',
                'properties': {'account': {'$ref': '#/definitions/Account'}},
                'required': ['account'],
            },
        },
    }


def test_forward_ref_with_field(create_module):
    @create_module
    def module():
        from typing import List

        import pytest

        from pydantic import BaseModel, Field
        from pydantic.typing import ForwardRef

        Foo = ForwardRef('Foo')

        with pytest.raises(
            ValueError, match='On field "c" the following field constraints are set but not enforced: gt.'
        ):

            class Foo(BaseModel):
                c: List[Foo] = Field(..., gt=0)


@skip_pre_37
def test_forward_ref_optional(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class Spec(BaseModel):
    spec_fields: List[str] = Field(..., alias="fields")
    filter: Optional[str]
    sort: Optional[str]


class PSpec(Spec):
    g: Optional[GSpec]


class GSpec(Spec):
    p: Optional[PSpec]

PSpec.update_forward_refs()

class Filter(BaseModel):
    g: Optional[GSpec]
    p: Optional[PSpec]
    """
    )
    Filter = module.Filter
    assert isinstance(Filter(p={'sort': 'some_field:asc', 'fields': []}), Filter)


def test_forward_ref_with_create_model(create_module):
    @create_module
    def module():
        import pydantic

        Sub = pydantic.create_model('Sub', foo='bar', __module__=__name__)
        assert Sub  # get rid of "local variable 'Sub' is assigned to but never used"
        Main = pydantic.create_model('Main', sub=('Sub', ...), __module__=__name__)
        instance = Main(sub={})
        assert instance.sub.dict() == {'foo': 'bar'}


@skip_pre_37
def test_resolve_forward_ref_dataclass(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel
from pydantic.typing import Literal

@dataclass
class Base:
    literal: Literal[1, 2]

class What(BaseModel):
    base: Base
        """
    )

    m = module.What(base=module.Base(literal=1))
    assert m.base.literal == 1


def test_nested_forward_ref():
    class NestedTuple(BaseModel):
        x: Tuple[int, Optional['NestedTuple']]  # noqa: F821

    with pytest.raises(ConfigError) as exc_info:
        NestedTuple.parse_obj({'x': ('1', {'x': ('2', {'x': ('3', None)})})})
    assert str(exc_info.value) == (
        'field "x_1" not yet prepared so type is still a ForwardRef, '
        'you might need to call NestedTuple.update_forward_refs().'
    )

    NestedTuple.update_forward_refs()
    obj = NestedTuple.parse_obj({'x': ('1', {'x': ('2', {'x': ('3', None)})})})
    assert obj.dict() == {'x': (1, {'x': (2, {'x': (3, None)})})}


@pytest.mark.skipif(future_typing is None, reason='`future_typing` is not installed')
@skip_pre_37
def test_forward_ref_future_typing(create_module):
    m = create_module(
        # language=Python
        """
from __future__ import annotations

from typing_extensions import Literal

from pydantic import BaseModel, Field

class User(BaseModel, validate_assignment=True):
    first_name: int | str
    last_name: str | None = None
    friends: list[User] = Field(default_factory=list)
    metadata: dict[str, int] | None = None
    number: Literal[42] = 42

user = User(first_name='pika', last_name=666, number=42)
"""
    )
    assert m.user.last_name == '666'
    assert m.user.friends == []
    m.user.metadata = {b'1': b'1'}
    assert m.user.metadata == {'1': 1}
    with pytest.raises(ValidationError):
        m.user.last_name = ['chu']
    with pytest.raises(ValidationError):
        m.user.number = 43


@pytest.mark.skipif(future_typing is not None, reason='`future_typing` is installed')
@skip_pre_37
def test_forward_ref_no_future_typing(create_module):
    with pytest.raises(TypeError, match="unsupported operand type(s) for |: 'type' and 'type'"):
        with pytest.warns(UserWarning, match='you need to install `pydantic[future-annotations]`'):
            create_module(
                # language=Python
                """
from __future__ import annotations

from pydantic import BaseModel, Field

class User(BaseModel, validate_assignment=True):
    first_name: int | str
    last_name: str | None = None
    friends: list[User] = Field(default_factory=list)
    metadata: dict[str, int] | None = None

user = User(first_name='pika', last_name=666)
                """
            )
