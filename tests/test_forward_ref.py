import sys
from typing import Optional, Tuple

import pytest
from dirty_equals import IsStr

from pydantic import BaseModel, PydanticUserError, ValidationError


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


def test_postponed_annotations_auto_model_rebuild(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

class Model(BaseModel):
    a: Model
"""
    )
    assert module.Model.__fields__['a'].annotation.__name__ == 'SelfType'


def test_forward_ref_auto_update_no_model(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Foo(BaseModel):
            a: 'Bar' = None

        class Bar(BaseModel):
            b: 'Foo'

    assert module.Foo.__pydantic_model_complete__ is False
    assert module.Bar.__pydantic_model_complete__ is True
    assert repr(module.Bar.__fields__['b']) == 'FieldInfo(annotation=Foo, required=True)'

    # Bar should be complet and ready to use
    b = module.Bar(b={'a': {'b': {}}})
    assert b == {'b': {'a': {'b': {'a': None}}}}

    # __field__ is complete on Foo
    assert repr(module.Foo.__fields__['a']).startswith(
        'FieldInfo(annotation=SelfType, required=False, metadata=[SchemaRef(__pydantic_validation_schema__'
    )
    # but Foo is not ready to use
    with pytest.raises(PydanticUserError, match='`Foo` is not fully defined, you should define `Bar`,'):
        module.Foo(a={'b': {'a': {}}})

    assert module.Foo.model_rebuild() is True
    assert module.Foo.__pydantic_model_complete__ is True

    # now Foo is ready to use
    f = module.Foo(a={'b': {'a': {'b': {}}}})
    assert f == {'a': {'b': {'a': {'b': {'a': None}}}}}


def test_forward_ref_one_of_fields_not_defined(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Foo(BaseModel):
            foo: 'Foo'
            bar: 'Bar'  # noqa: F821

    assert hasattr(module.Foo, '__fields__') is False


def test_basic_forward_ref(create_module):
    @create_module
    def module():
        from typing import ForwardRef, Optional

        from pydantic import BaseModel

        class Foo(BaseModel):
            a: int

        FooRef = ForwardRef('Foo')

        class Bar(BaseModel):
            b: Optional[FooRef] = None

    assert module.Bar().dict() == {'b': None}
    assert module.Bar(b={'a': '123'}).dict() == {'b': {'a': 123}}


def test_self_forward_ref_module(create_module):
    @create_module
    def module():
        from typing import ForwardRef

        from pydantic import BaseModel

        FooRef = ForwardRef('Foo')

        class Foo(BaseModel):
            a: int = 123
            b: FooRef = None

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

    assert module.Foo().dict() == {'a': 123, 'b': None, 'c': [], 'd': {}}
    assert module.Foo(b={'a': '321'}, c=[{'a': 234}], d={'bar': {'a': 345}}).dict() == {
        'a': 123,
        'b': {'a': 321, 'b': None, 'c': [], 'd': {}},
        'c': [{'a': 234, 'b': None, 'c': [], 'd': {}}],
        'd': {'bar': {'a': 345, 'b': None, 'c': [], 'd': {}}},
    }

    with pytest.raises(ValidationError) as exc_info:
        module.Foo(b={'a': '321'}, c=[{'b': 234}], d={'bar': {'a': 345}})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'dict_type', 'loc': ('c', 0, 'b'), 'msg': 'Input should be a valid dictionary', 'input': 234}
    ]

    assert repr(module.Foo.__fields__['a']) == 'FieldInfo(annotation=int, required=False, default=123)'
    assert repr(module.Foo.__fields__['b']) == IsStr(
        regex=r'FieldInfo\(annotation=SelfType, required=False, metadata=\[Schem.+.Foo\'\}\}\)\]\)'
    )
    if sys.version_info < (3, 10):
        return
    assert repr(module.Foo.__fields__['c']) == IsStr(regex=r'FieldInfo\(annotation=List\[Annotated\[SelfType.+')
    assert repr(module.Foo.__fields__['d']) == IsStr(
        regex=r'FieldInfo\(annotation=Dict\[str, Annotated\[SelfType, SchemaRef.*'
    )


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

            return Foo

    Foo = module.main()
    assert Foo().dict() == {'a': 123, 'b': None}
    assert Foo(b={'a': '321'}).dict() == {'a': 123, 'b': {'a': 321, 'b': None}}


@pytest.mark.xfail(reason='TODO dataclasses')
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


@pytest.mark.xfail(reason='TODO dataclasses')
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


@pytest.mark.xfail(reason='TODO schema')
def test_self_reference_json_schema(create_module):
    @create_module
    def module():
        from typing import List

        from pydantic import BaseModel

        class Account(BaseModel):
            name: str
            subaccounts: List['Account'] = []

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


@pytest.mark.xfail(reason='TODO schema')
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


@pytest.mark.xfail(reason='TODO schema')
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


@pytest.mark.xfail(reason='TODO schema')
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
        from pydantic_core import SchemaError

        from pydantic import BaseModel, Field

        Foo = ForwardRef('Foo')

        with pytest.raises(SchemaError, match=r'Extra inputs are not permitted \[type=extra_forbidden,'):

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
    filter: Optional[str] = None
    sort: Optional[str]


class PSpec(Spec):
    g: Optional[GSpec]


class GSpec(Spec):
    p: Optional[PSpec]

# PSpec.model_rebuild()

class Filter(BaseModel):
    g: Optional[GSpec] = None
    p: Optional[PSpec]
    """
    )
    Filter = module.Filter
    assert isinstance(Filter(p={'sort': 'some_field:asc', 'fields': []}), Filter)


@pytest.mark.xfail(reason='TODO create_model')
def test_forward_ref_with_create_model(create_module):
    @create_module
    def module():
        import pydantic

        Sub = pydantic.create_model('Sub', foo='bar', __module__=__name__)
        assert Sub  # get rid of "local variable 'Sub' is assigned to but never used"
        Main = pydantic.create_model('Main', sub=('Sub', ...), __module__=__name__)
        instance = Main(sub={})
        assert instance.sub.dict() == {'foo': 'bar'}


@pytest.mark.xfail(reason='TODO dataclasses')
def test_resolve_forward_ref_dataclass(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel
from typing_extensions import Literal

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


@pytest.mark.xfail(reason='TODO discriminator')
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

    with pytest.raises(PydanticUserError, match='`Pet` is not fully defined, you should define `Cat`'):
        module.Pet.parse_obj({'type': 'pika'})

    module.Pet.model_rebuild()

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


@pytest.mark.xfail(reason='TODO class_vars')
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


@pytest.mark.xfail(reason='TODO json encoding')
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


@pytest.mark.xfail(reason='TODO json encoding')
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
def test_pep585_self_referencing_generics(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

class SelfReferencing(BaseModel):
    names: list[SelfReferencing]  # noqa: F821
"""
    )

    SelfReferencing = module.SelfReferencing
    if sys.version_info >= (3, 10):
        assert repr(SelfReferencing.__fields__['names']) == IsStr(
            regex=r'FieldInfo\(annotation=list\[Annotated\[SelfType, SchemaRef.+, required=True\)'
        )
    # test that object creation works
    obj = SelfReferencing(names=[SelfReferencing(names=[])])
    assert obj.names == [SelfReferencing(names=[])]


@skip_pep585
def test_pep585_recursive_generics(create_module):
    @create_module
    def module():
        from typing import ForwardRef

        from pydantic import BaseModel

        HeroRef = ForwardRef('Hero')

        class Team(BaseModel):
            name: str
            heroes: list[HeroRef]  # noqa: F821

        class Hero(BaseModel):
            name: str
            teams: list[Team]

        Team.model_rebuild()

    assert repr(module.Team.__fields__['heroes']) == 'FieldInfo(annotation=list[Hero], required=True)'
    assert repr(module.Hero.__fields__['teams']) == 'FieldInfo(annotation=list[Team], required=True)'

    h = module.Hero(name='Ivan', teams=[module.Team(name='TheBest', heroes=[])])
    # insert_assert(h.dict())
    assert h.dict() == {'name': 'Ivan', 'teams': [{'name': 'TheBest', 'heroes': []}]}


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


def test_recursive_model(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class Foobar(BaseModel):
    x: int
    y: Optional[Foobar] = None
"""
    )
    f = module.Foobar(x=1, y={'x': 2})
    assert f.dict() == {'x': 1, 'y': {'x': 2, 'y': None}}
    assert f.__fields_set__ == {'x', 'y'}
    assert f.y.__fields_set__ == {'x'}


def test_force_rebuild():
    class Foobar(BaseModel):
        b: int

    assert Foobar.__pydantic_model_complete__ is True
    assert Foobar.model_rebuild() is None
    assert Foobar.model_rebuild(force=True) is True


def test_nested_annotation(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

def nested():
    class Foo(BaseModel):
        a: int

    class Bar(BaseModel):
        b: Foo

    return Bar
"""
    )

    bar_model = module.nested()
    assert bar_model.__pydantic_model_complete__ is True
    assert bar_model(b={'a': 1}).dict() == {'b': {'a': 1}}


def test_nested_more_annotation(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        def nested():
            class Foo(BaseModel):
                a: int

            def more_nested():
                class Bar(BaseModel):
                    b: 'Foo'

                return Bar

            return more_nested()

    bar_model = module.nested()
    # this does not work because Foo is in a parent scope
    assert bar_model.__pydantic_model_complete__ is False


def test_nested_annotation_priority(create_module):
    @create_module
    def module():
        from annotated_types import Gt
        from typing_extensions import Annotated

        from pydantic import BaseModel

        Foobar = Annotated[int, Gt(0)]  # noqa: F841

        def nested():
            Foobar = Annotated[int, Gt(10)]

            class Bar(BaseModel):
                b: 'Foobar'

            return Bar

    bar_model = module.nested()
    assert bar_model.__fields__['b'].metadata[0].gt == 10
    assert bar_model(b=11).dict() == {'b': 11}
    with pytest.raises(ValidationError, match=r'Input should be greater than 10 \[type=greater_than,'):
        bar_model(b=1)


def test_nested_model_rebuild(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        def nested():
            class Bar(BaseModel):
                b: 'Foo'

            class Foo(BaseModel):
                a: int

            assert Bar.__pydantic_model_complete__ is False
            Bar.model_rebuild()
            return Bar

    bar_model = module.nested()
    assert bar_model.__pydantic_model_complete__ is True
    assert bar_model(b={'a': 1}).dict() == {'b': {'a': 1}}
