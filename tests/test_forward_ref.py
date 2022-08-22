import sys
from typing import Dict, ForwardRef, List, Optional, Tuple

import pytest

from pydantic import BaseModel, ConfigError, ValidationError


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


def test_postponed_annotations_auto_update_forward_refs(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

class Model(BaseModel):
    a: Model
"""
    )

    assert module.Model.__fields__['a'].type_ is module.Model


def test_forward_ref_auto_update_no_model(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import BaseModel

class Foo(BaseModel):
    a: 'Bar'

class Bar(BaseModel):
    b: 'Foo'
"""
    )

    assert module.Foo.__fields__['a'].type_ == ForwardRef('Bar')
    assert module.Bar.__fields__['b'].type_ is module.Foo


def test_forward_ref_one_of_fields_not_defined(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Foo(BaseModel):
            foo: 'Foo'
            bar: 'Bar'  # noqa: F821

    assert module.Foo.__fields__['bar'].type_ == ForwardRef('Bar')
    assert module.Foo.__fields__['foo'].type_ is module.Foo


def test_basic_forward_ref(create_module):
    @create_module
    def module():
        from typing import ForwardRef, Optional

        from pydantic import BaseModel

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
        from typing import ForwardRef

        from pydantic import BaseModel

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

        class Foo(BaseModel):
            a: int = 123
            b: 'Foo' = None
            c: 'List[Foo]' = []
            d: 'Dict[str, Foo]' = {}

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

    assert module.Foo.__fields__['a'].type_ is int
    assert module.Foo.__fields__['b'].type_ is module.Foo
    assert module.Foo.__fields__['b'].outer_type_ is module.Foo
    assert module.Foo.__fields__['c'].type_ is module.Foo
    assert module.Foo.__fields__['c'].outer_type_ == List[module.Foo]
    assert module.Foo.__fields__['d'].type_ is module.Foo
    assert module.Foo.__fields__['d'].outer_type_ == Dict[str, module.Foo]


def test_self_forward_ref_local(create_module):
    @create_module
    def module():
        from typing import ForwardRef

        from pydantic import BaseModel

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
        from typing import ForwardRef

        from pydantic import BaseModel

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

    Node = module.Node
    Leaf = module.Leaf
    data = {'value': 3, 'left': {'a': 'foo'}, 'right': {'value': 5, 'left': {'a': 'bar'}, 'right': {'a': 'buzz'}}}

    node = Node(**data)
    assert isinstance(node.left, Leaf)
    assert isinstance(node.right, Node)


def test_forward_ref_nested_sub_types(create_module):
    @create_module
    def module():
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
        from typing import ForwardRef, List

        import pytest

        from pydantic import BaseModel, Field

        Foo = ForwardRef('Foo')

        with pytest.raises(
            ValueError, match='On field "c" the following field constraints are set but not enforced: gt.'
        ):

            class Foo(BaseModel):
                c: List[Foo] = Field(..., gt=0)


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

    obj = NestedTuple.parse_obj({'x': ('1', {'x': ('2', {'x': ('3', None)})})})
    assert obj.dict() == {'x': (1, {'x': (2, {'x': (3, None)})})}


def test_discriminated_union_forward_ref(create_module):
    @create_module
    def module():
        from typing import Union

        from typing_extensions import Literal

        from pydantic import BaseModel, Field

        class Pet(BaseModel):
            __root__: Union['Cat', 'Dog'] = Field(..., discriminator='type')  # noqa: F821

        class Cat(BaseModel):
            type: Literal['cat']

        class Dog(BaseModel):
            type: Literal['dog']

    with pytest.raises(ConfigError, match='you might need to call Pet.update_forward_refs()'):
        module.Pet.parse_obj({'type': 'pika'})

    module.Pet.update_forward_refs()

    with pytest.raises(ValidationError, match="No match for discriminator 'type' and value 'pika'"):
        module.Pet.parse_obj({'type': 'pika'})

    assert module.Pet.schema() == {
        'title': 'Pet',
        'discriminator': {'propertyName': 'type', 'mapping': {'cat': '#/definitions/Cat', 'dog': '#/definitions/Dog'}},
        'oneOf': [{'$ref': '#/definitions/Cat'}, {'$ref': '#/definitions/Dog'}],
        'definitions': {
            'Cat': {
                'title': 'Cat',
                'type': 'object',
                'properties': {'type': {'title': 'Type', 'enum': ['cat'], 'type': 'string'}},
                'required': ['type'],
            },
            'Dog': {
                'title': 'Dog',
                'type': 'object',
                'properties': {'type': {'title': 'Type', 'enum': ['dog'], 'type': 'string'}},
                'required': ['type'],
            },
        },
    }


def test_class_var_as_string(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import ClassVar
from pydantic import BaseModel

class Model(BaseModel):
    a: ClassVar[int]
"""
    )

    assert module.Model.__class_vars__ == {'a'}


def test_json_encoder_str(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import BaseModel


class User(BaseModel):
    x: str


FooUser = User


class User(BaseModel):
    y: str


class Model(BaseModel):
    foo_user: FooUser
    user: User

    class Config:
        json_encoders = {
            'User': lambda v: f'User({v.y})',
        }
"""
    )

    m = module.Model(foo_user={'x': 'user1'}, user={'y': 'user2'})
    assert m.json(models_as_dict=False) == '{"foo_user": {"x": "user1"}, "user": "User(user2)"}'


def test_json_encoder_forward_ref(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import BaseModel
from typing import ForwardRef, List, Optional

class User(BaseModel):
    name: str
    friends: Optional[List['User']] = None

    class Config:
        json_encoders = {
            ForwardRef('User'): lambda v: f'User({v.name})',
        }
"""
    )

    m = module.User(name='anne', friends=[{'name': 'ben'}, {'name': 'charlie'}])
    assert m.json(models_as_dict=False) == '{"name": "anne", "friends": ["User(ben)", "User(charlie)"]}'


skip_pep585 = pytest.mark.skipif(
    sys.version_info < (3, 9), reason='PEP585 generics only supported for python 3.9 and above'
)


@skip_pep585
def test_pep585_self_referencing_generics():
    class SelfReferencing(BaseModel):
        names: list['SelfReferencing']  # noqa: F821

    SelfReferencing.update_forward_refs()  # will raise an exception if the forward ref isn't resolvable
    # test the class
    assert SelfReferencing.__fields__['names'].type_ is SelfReferencing
    # NOTE: outer_type_ is not converted
    assert SelfReferencing.__fields__['names'].outer_type_ == list['SelfReferencing']
    # test that object creation works
    obj = SelfReferencing(names=[SelfReferencing(names=[])])
    assert obj.names == [SelfReferencing(names=[])]


@skip_pep585
def test_pep585_recursive_generics(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Team(BaseModel):
            name: str
            heroes: list['Hero']  # noqa: F821

        class Hero(BaseModel):
            name: str
            teams: list[Team]

        Team.update_forward_refs()

    assert module.Team.__fields__['heroes'].type_ is module.Hero
    assert module.Hero.__fields__['teams'].type_ is module.Team

    module.Hero(name='Ivan', teams=[module.Team(name='TheBest', heroes=[])])


@pytest.mark.skipif(sys.version_info < (3, 9), reason='needs 3.9 or newer')
def test_class_var_forward_ref(create_module):
    # see #3679
    create_module(
        # language=Python
        """
from __future__ import annotations
from typing import ClassVar
from pydantic import BaseModel

class WithClassVar(BaseModel):
    Instances: ClassVar[dict[str, WithClassVar]] = {}
"""
    )
