import dataclasses
import re
import sys
import typing
from typing import Any, Optional

import pytest

from pydantic import BaseModel, PydanticUserError, TypeAdapter, ValidationError


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
    assert m.model_dump() == {'a': 123}


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
    assert module.Model.model_fields['a'].annotation.__name__ == 'Model'


def test_forward_ref_auto_update_no_model(create_module):
    @create_module
    def module():
        from typing import Optional

        import pytest

        from pydantic import BaseModel, PydanticUserError

        class Foo(BaseModel):
            a: Optional['Bar'] = None

        with pytest.raises(PydanticUserError, match='`Foo` is not fully defined; you should define `Bar`,'):
            Foo(a={'b': {'a': {}}})

        class Bar(BaseModel):
            b: 'Foo'

    assert module.Bar.__pydantic_complete__ is True
    assert repr(module.Bar.model_fields['b']) == 'FieldInfo(annotation=Foo, required=True)'

    # Bar should be complete and ready to use
    b = module.Bar(b={'a': {'b': {}}})
    assert b.model_dump() == {'b': {'a': {'b': {'a': None}}}}

    # model_fields is complete on Foo
    assert repr(module.Foo.model_fields['a']) == (
        'FieldInfo(annotation=Union[Bar, NoneType], required=False, default=None)'
    )

    assert module.Foo.__pydantic_complete__ is False
    # Foo gets auto-rebuilt during the first attempt at validation
    f = module.Foo(a={'b': {'a': {'b': {'a': None}}}})
    assert module.Foo.__pydantic_complete__ is True
    assert f.model_dump() == {'a': {'b': {'a': {'b': {'a': None}}}}}


def test_forward_ref_one_of_fields_not_defined(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Foo(BaseModel):
            foo: 'Foo'
            bar: 'Bar'

    assert {k: repr(v) for k, v in module.Foo.model_fields.items()} == {
        'foo': 'FieldInfo(annotation=Foo, required=True)',
        'bar': "FieldInfo(annotation=ForwardRef('Bar'), required=True)",
    }


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

    assert module.Bar().model_dump() == {'b': None}
    assert module.Bar(b={'a': '123'}).model_dump() == {'b': {'a': 123}}


def test_self_forward_ref_module(create_module):
    @create_module
    def module():
        from typing import ForwardRef, Optional

        from pydantic import BaseModel

        FooRef = ForwardRef('Foo')

        class Foo(BaseModel):
            a: int = 123
            b: Optional[FooRef] = None

    assert module.Foo().model_dump() == {'a': 123, 'b': None}
    assert module.Foo(b={'a': '321'}).model_dump() == {'a': 123, 'b': {'a': 321, 'b': None}}


def test_self_forward_ref_collection(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Foo(BaseModel):
            a: int = 123
            b: 'Foo' = None
            c: 'list[Foo]' = []
            d: 'dict[str, Foo]' = {}

    assert module.Foo().model_dump() == {'a': 123, 'b': None, 'c': [], 'd': {}}
    assert module.Foo(b={'a': '321'}, c=[{'a': 234}], d={'bar': {'a': 345}}).model_dump() == {
        'a': 123,
        'b': {'a': 321, 'b': None, 'c': [], 'd': {}},
        'c': [{'a': 234, 'b': None, 'c': [], 'd': {}}],
        'd': {'bar': {'a': 345, 'b': None, 'c': [], 'd': {}}},
    }

    with pytest.raises(ValidationError) as exc_info:
        module.Foo(b={'a': '321'}, c=[{'b': 234}], d={'bar': {'a': 345}})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('c', 0, 'b'),
            'msg': 'Input should be a valid dictionary or instance of Foo',
            'input': 234,
            'ctx': {'class_name': 'Foo'},
        }
    ]

    assert repr(module.Foo.model_fields['a']) == 'FieldInfo(annotation=int, required=False, default=123)'
    assert repr(module.Foo.model_fields['b']) == 'FieldInfo(annotation=Foo, required=False, default=None)'
    if sys.version_info < (3, 10):
        return
    assert repr(module.Foo.model_fields['c']) == ('FieldInfo(annotation=list[Foo], required=False, default=[])')
    assert repr(module.Foo.model_fields['d']) == ('FieldInfo(annotation=dict[str, Foo], required=False, default={})')


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
    assert Foo().model_dump() == {'a': 123, 'b': None}
    assert Foo(b={'a': '321'}).model_dump() == {'a': 123, 'b': {'a': 321, 'b': None}}


def test_forward_ref_dataclass(create_module):
    @create_module
    def module():
        from typing import Optional

        from pydantic.dataclasses import dataclass

        @dataclass
        class MyDataclass:
            a: int
            b: Optional['MyDataclass'] = None

    dc = module.MyDataclass(a=1, b={'a': 2, 'b': {'a': 3}})
    assert dataclasses.asdict(dc) == {'a': 1, 'b': {'a': 2, 'b': {'a': 3, 'b': None}}}


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
        from typing import ForwardRef, Union

        from pydantic import BaseModel

        class Leaf(BaseModel):
            a: str

        TreeType = Union[Union[tuple[ForwardRef('Node'), str], int], Leaf]

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


def test_self_reference_json_schema(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Account(BaseModel):
            name: str
            subaccounts: list['Account'] = []

    Account = module.Account
    assert Account.model_json_schema() == {
        '$ref': '#/$defs/Account',
        '$defs': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/$defs/Account'},
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
from pydantic import BaseModel

class Account(BaseModel):
  name: str
  subaccounts: list[Account] = []
    """
    )
    Account = module.Account
    assert Account.model_json_schema() == {
        '$ref': '#/$defs/Account',
        '$defs': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/$defs/Account'},
                    },
                },
                'required': ['name'],
            }
        },
    }


def test_circular_reference_json_schema(create_module):
    @create_module
    def module():
        from pydantic import BaseModel

        class Owner(BaseModel):
            account: 'Account'

        class Account(BaseModel):
            name: str
            owner: 'Owner'
            subaccounts: list['Account'] = []

    Account = module.Account
    assert Account.model_json_schema() == {
        '$ref': '#/$defs/Account',
        '$defs': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'owner': {'$ref': '#/$defs/Owner'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/$defs/Account'},
                    },
                },
                'required': ['name', 'owner'],
            },
            'Owner': {
                'title': 'Owner',
                'type': 'object',
                'properties': {'account': {'$ref': '#/$defs/Account'}},
                'required': ['account'],
            },
        },
    }


def test_circular_reference_json_schema_with_future_annotations(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

class Owner(BaseModel):
  account: Account

class Account(BaseModel):
  name: str
  owner: Owner
  subaccounts: list[Account] = []

    """
    )
    Account = module.Account
    assert Account.model_json_schema() == {
        '$ref': '#/$defs/Account',
        '$defs': {
            'Account': {
                'title': 'Account',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'owner': {'$ref': '#/$defs/Owner'},
                    'subaccounts': {
                        'title': 'Subaccounts',
                        'default': [],
                        'type': 'array',
                        'items': {'$ref': '#/$defs/Account'},
                    },
                },
                'required': ['name', 'owner'],
            },
            'Owner': {
                'title': 'Owner',
                'type': 'object',
                'properties': {'account': {'$ref': '#/$defs/Account'}},
                'required': ['account'],
            },
        },
    }


def test_forward_ref_with_field(create_module):
    @create_module
    def module():
        import re
        from typing import ForwardRef

        import pytest

        from pydantic import BaseModel, Field

        Foo = ForwardRef('Foo')

        class Foo(BaseModel):
            c: list[Foo] = Field(gt=0)

        with pytest.raises(TypeError, match=re.escape("Unable to apply constraint 'gt' to supplied value []")):
            Foo(c=[Foo(c=[])])


def test_forward_ref_optional(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel, Field


class Spec(BaseModel):
    spec_fields: list[str] = Field(alias="fields")
    filter: str | None = None
    sort: str | None


class PSpec(Spec):
    g: GSpec | None = None


class GSpec(Spec):
    p: PSpec | None

# PSpec.model_rebuild()

class Filter(BaseModel):
    g: GSpec | None = None
    p: PSpec | None
    """
    )
    Filter = module.Filter
    assert isinstance(Filter(p={'sort': 'some_field:asc', 'fields': []}), Filter)


def test_forward_ref_with_create_model(create_module):
    @create_module
    def module():
        import pydantic

        Sub = pydantic.create_model('Sub', foo=(str, 'bar'), __module__=__name__)
        assert Sub  # get rid of "local variable 'Sub' is assigned to but never used"
        Main = pydantic.create_model('Main', sub=('Sub', ...), __module__=__name__)
        instance = Main(sub={})
        assert instance.sub.model_dump() == {'foo': 'bar'}


def test_resolve_forward_ref_dataclass(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel
from typing import Literal

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
        x: tuple[int, Optional['NestedTuple']]

    obj = NestedTuple.model_validate({'x': ('1', {'x': ('2', {'x': ('3', None)})})})
    assert obj.model_dump() == {'x': (1, {'x': (2, {'x': (3, None)})})}


def test_discriminated_union_forward_ref(create_module):
    @create_module
    def module():
        from typing import Literal, Union

        from pydantic import BaseModel, Field

        class Pet(BaseModel):
            pet: Union['Cat', 'Dog'] = Field(discriminator='type')

        class Cat(BaseModel):
            type: Literal['cat']

        class Dog(BaseModel):
            type: Literal['dog']

    assert module.Pet.__pydantic_complete__ is False

    with pytest.raises(
        ValidationError,
        match="Input tag 'pika' found using 'type' does not match any of the expected tags: 'cat', 'dog'",
    ):
        module.Pet.model_validate({'pet': {'type': 'pika'}})

    # Ensure the rebuild has happened automatically despite validation failure
    assert module.Pet.__pydantic_complete__ is True

    # insert_assert(module.Pet.model_json_schema())
    assert module.Pet.model_json_schema() == {
        'title': 'Pet',
        'required': ['pet'],
        'type': 'object',
        'properties': {
            'pet': {
                'title': 'Pet',
                'discriminator': {'mapping': {'cat': '#/$defs/Cat', 'dog': '#/$defs/Dog'}, 'propertyName': 'type'},
                'oneOf': [{'$ref': '#/$defs/Cat'}, {'$ref': '#/$defs/Dog'}],
            }
        },
        '$defs': {
            'Cat': {
                'title': 'Cat',
                'type': 'object',
                'properties': {'type': {'const': 'cat', 'title': 'Type', 'type': 'string'}},
                'required': ['type'],
            },
            'Dog': {
                'title': 'Dog',
                'type': 'object',
                'properties': {'type': {'const': 'dog', 'title': 'Type', 'type': 'string'}},
                'required': ['type'],
            },
        },
    }


def test_class_var_as_string(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import Annotated, ClassVar, ClassVar as CV
from pydantic import BaseModel

class Model(BaseModel):
    a: ClassVar[int]
    _b: ClassVar[int]
    _c: ClassVar[Forward]
    _d: Annotated[ClassVar[int], ...]
    _e: CV[int]
    _f: Annotated[CV[int], ...]
    # Doesn't work as of today:
    # _g: CV[Forward]

Forward = int
"""
    )

    assert module.Model.__class_vars__ == {'a', '_b', '_c', '_d', '_e', '_f'}
    assert module.Model.__private_attributes__ == {}


def test_private_attr_annotation_not_evaluated() -> None:
    class Model(BaseModel):
        _a: 'UnknownAnnotation'

    assert '_a' in Model.__private_attributes__


def test_json_encoder_str(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import BaseModel, ConfigDict, field_serializer


class User(BaseModel):
    x: str


FooUser = User


class User(BaseModel):
    y: str


class Model(BaseModel):
    foo_user: FooUser
    user: User

    @field_serializer('user')
    def serialize_user(self, v):
        return f'User({v.y})'

"""
    )

    m = module.Model(foo_user={'x': 'user1'}, user={'y': 'user2'})
    # TODO: How can we replicate this custom-encoder functionality without affecting the serialization of `User`?
    assert m.model_dump_json() == '{"foo_user":{"x":"user1"},"user":"User(user2)"}'


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
        assert (
            repr(SelfReferencing.model_fields['names']) == 'FieldInfo(annotation=list[SelfReferencing], required=True)'
        )

    # test that object creation works
    obj = SelfReferencing(names=[SelfReferencing(names=[])])
    assert obj.names == [SelfReferencing(names=[])]


def test_pep585_recursive_generics(create_module):
    @create_module
    def module():
        from typing import ForwardRef

        from pydantic import BaseModel

        HeroRef = ForwardRef('Hero')

        class Team(BaseModel):
            name: str
            heroes: list[HeroRef]

        class Hero(BaseModel):
            name: str
            teams: list[Team]

        Team.model_rebuild()

    assert repr(module.Team.model_fields['heroes']) == 'FieldInfo(annotation=list[Hero], required=True)'
    assert repr(module.Hero.model_fields['teams']) == 'FieldInfo(annotation=list[Team], required=True)'

    h = module.Hero(name='Ivan', teams=[module.Team(name='TheBest', heroes=[])])
    # insert_assert(h.model_dump())
    assert h.model_dump() == {'name': 'Ivan', 'teams': [{'name': 'TheBest', 'heroes': []}]}


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
    assert f.model_dump() == {'x': 1, 'y': {'x': 2, 'y': None}}
    assert f.model_fields_set == {'x', 'y'}
    assert f.y.model_fields_set == {'x'}


@pytest.mark.skipif(sys.version_info < (3, 10), reason='needs 3.10 or newer')
def test_recursive_models_union(create_module):
    # This test should pass because PydanticRecursiveRef.__or__ is implemented,
    # not because `eval_type_backport` magically makes `|` work,
    # since it's installed for tests but otherwise optional.
    # When generic models are involved in recursive models, parametrizing a model
    # can result in a `PydanticRecursiveRef` instance. This isn't ideal, as in the
    # example below, this results in the `FieldInfo.annotation` attribute being changed,
    # e.g. for `bar` to something like `PydanticRecursiveRef(...) | None`.
    # We currently have a workaround (avoid caching parametrized models where this bad
    # annotation mutation can happen).
    sys.modules['eval_type_backport'] = None  # type: ignore
    try:
        create_module(
            # language=Python
            """
from __future__ import annotations

from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class Foo(BaseModel):
    bar: Bar[str] | None = None
    bar2: int | Bar[float]

class Bar(BaseModel, Generic[T]):
    foo: Foo
    """
        )
    finally:
        del sys.modules['eval_type_backport']


def test_recursive_models_union_backport(create_module):
    create_module(
        # language=Python
        """
from __future__ import annotations

from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class Foo(BaseModel):
    bar: Bar[str] | None = None
    # The `int | str` here differs from the previous test and requires the backport.
    # At the same time, `PydanticRecursiveRef.__or__` means that the second `|` works normally,
    # which actually triggered a bug in the backport that needed fixing.
    bar2: int | str | Bar[float]

class Bar(BaseModel, Generic[T]):
    foo: Foo
"""
    )


def test_force_rebuild():
    class Foobar(BaseModel):
        b: int

    assert Foobar.__pydantic_complete__ is True
    assert Foobar.model_rebuild() is None
    assert Foobar.model_rebuild(force=True) is True


def test_rebuild_subclass_of_built_model():
    class Model(BaseModel):
        x: int

    class FutureReferencingModel(Model):
        y: 'FutureModel'

    class FutureModel(BaseModel):
        pass

    FutureReferencingModel.model_rebuild()

    assert FutureReferencingModel(x=1, y=FutureModel()).model_dump() == {'x': 1, 'y': {}}


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
    assert bar_model.__pydantic_complete__ is True
    assert bar_model(b={'a': 1}).model_dump() == {'b': {'a': 1}}


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
    assert bar_model.__pydantic_complete__ is False


def test_nested_annotation_priority(create_module):
    @create_module
    def module():
        from typing import Annotated

        from annotated_types import Gt

        from pydantic import BaseModel

        Foobar = Annotated[int, Gt(0)]  # noqa: F841

        def nested():
            Foobar = Annotated[int, Gt(10)]

            class Bar(BaseModel):
                b: 'Foobar'

            return Bar

    bar_model = module.nested()
    assert bar_model.model_fields['b'].metadata[0].gt == 10
    assert bar_model(b=11).model_dump() == {'b': 11}
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

            assert Bar.__pydantic_complete__ is False
            Bar.model_rebuild()
            return Bar

    bar_model = module.nested()
    assert bar_model.__pydantic_complete__ is True
    assert bar_model(b={'a': 1}).model_dump() == {'b': {'a': 1}}


def pytest_raises_user_error_for_undefined_type(defining_class_name, missing_type_name):
    """
    Returns a `pytest.raises` context manager that checks the error message when an undefined type is present.

    usage: `with pytest_raises_user_error_for_undefined_type(class_name='Foobar', missing_class_name='UndefinedType'):`
    """

    return pytest.raises(
        PydanticUserError,
        match=re.escape(
            f'`{defining_class_name}` is not fully defined; you should define `{missing_type_name}`, then call'
            f' `{defining_class_name}.model_rebuild()`.'
        ),
    )


#   NOTE: the `undefined_types_warning` tests below are "statically parameterized" (i.e. have Duplicate Code).
#   The initial attempt to refactor them into a single parameterized test was not straightforward due to the use of the
#   `create_module` fixture and the requirement that `from __future__ import annotations` be the first line in a module.
#
#   Test Parameters:
#     1. config setting: (1a) default behavior vs (1b) overriding with Config setting:
#     2. type checking approach: (2a) `from __future__ import annotations` vs (2b) `ForwardRef`
#
#   The parameter tags "1a", "1b", "2a", and "2b" are used in the test names below, to indicate which combination
#   of conditions the test is covering.


def test_undefined_types_warning_1a_raised_by_default_2a_future_annotations(create_module):
    with pytest_raises_user_error_for_undefined_type(defining_class_name='Foobar', missing_type_name='UndefinedType'):
        create_module(
            # language=Python
            """
from __future__ import annotations
from pydantic import BaseModel

class Foobar(BaseModel):
    a: UndefinedType

# Trigger the error for an undefined type:
Foobar(a=1)
"""
        )


def test_undefined_types_warning_1a_raised_by_default_2b_forward_ref(create_module):
    with pytest_raises_user_error_for_undefined_type(defining_class_name='Foobar', missing_type_name='UndefinedType'):

        @create_module
        def module():
            from typing import ForwardRef

            from pydantic import BaseModel

            UndefinedType = ForwardRef('UndefinedType')

            class Foobar(BaseModel):
                a: UndefinedType

            # Trigger the error for an undefined type
            Foobar(a=1)


def test_undefined_types_warning_1b_suppressed_via_config_2a_future_annotations(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

# Because we don't instantiate the type, no error for an undefined type is raised
class Foobar(BaseModel):
    a: UndefinedType
"""
    )
    # Since we're testing the absence of an error, it's important to confirm pydantic was actually run.
    # The presence of the `__pydantic_complete__` is a good indicator of this.
    assert module.Foobar.__pydantic_complete__ is False


def test_undefined_types_warning_1b_suppressed_via_config_2b_forward_ref(create_module):
    @create_module
    def module():
        from typing import ForwardRef

        from pydantic import BaseModel

        UndefinedType = ForwardRef('UndefinedType')

        # Because we don't instantiate the type, no error for an undefined type is raised
        class Foobar(BaseModel):
            a: UndefinedType

    # Since we're testing the absence of a warning, it's important to confirm pydantic was actually run.
    # The presence of the `__pydantic_complete__` is a good indicator of this.
    assert module.Foobar.__pydantic_complete__ is False


def test_undefined_types_warning_raised_by_usage(create_module):
    with pytest_raises_user_error_for_undefined_type('Foobar', 'UndefinedType'):

        @create_module
        def module():
            from typing import ForwardRef

            from pydantic import BaseModel

            UndefinedType = ForwardRef('UndefinedType')

            class Foobar(BaseModel):
                a: UndefinedType

            Foobar(a=1)


def test_rebuild_recursive_schema():
    from typing import ForwardRef

    class Expressions_(BaseModel):
        model_config = dict(undefined_types_warning=False)
        items: list["types['Expression']"]

    class Expression_(BaseModel):
        model_config = dict(undefined_types_warning=False)
        Or: ForwardRef("types['allOfExpressions']")
        Not: ForwardRef("types['allOfExpression']")

    class allOfExpression_(BaseModel):
        model_config = dict(undefined_types_warning=False)
        Not: ForwardRef("types['Expression']")

    class allOfExpressions_(BaseModel):
        model_config = dict(undefined_types_warning=False)
        items: list["types['Expression']"]

    types_namespace = {
        'types': {
            'Expression': Expression_,
            'Expressions': Expressions_,
            'allOfExpression': allOfExpression_,
            'allOfExpressions': allOfExpressions_,
        }
    }

    models = [allOfExpressions_, Expressions_]
    for m in models:
        m.model_rebuild(_types_namespace=types_namespace)


def test_forward_ref_in_generic(create_module: Any) -> None:
    """https://github.com/pydantic/pydantic/issues/6503"""

    @create_module
    def module():
        from pydantic import BaseModel

        class Foo(BaseModel):
            x: dict['type[Bar]', type['Bar']]

        class Bar(BaseModel):
            pass

    Foo = module.Foo
    Bar = module.Bar

    assert Foo(x={Bar: Bar}).x[Bar] is Bar


def test_forward_ref_in_generic_separate_modules(create_module: Any) -> None:
    """https://github.com/pydantic/pydantic/issues/6503"""

    @create_module
    def module_1():
        from pydantic import BaseModel

        class Foo(BaseModel):
            x: dict['type[Bar]', type['Bar']]

    @create_module
    def module_2():
        from pydantic import BaseModel

        class Bar(BaseModel):
            pass

    Foo = module_1.Foo
    Bar = module_2.Bar
    Foo.model_rebuild(_types_namespace={'tp': typing, 'Bar': Bar})
    assert Foo(x={Bar: Bar}).x[Bar] is Bar


def test_invalid_forward_ref() -> None:
    class CustomType:
        """A custom type that isn't subscriptable."""

    msg = "Unable to evaluate type annotation 'CustomType[int]'."

    with pytest.raises(TypeError, match=re.escape(msg)):

        class Model(BaseModel):
            foo: 'CustomType[int]'


def test_pydantic_extra_forward_ref_separate_module(create_module: Any) -> None:
    """https://github.com/pydantic/pydantic/issues/10069"""

    @create_module
    def module_1():
        from pydantic import BaseModel, ConfigDict

        class Bar(BaseModel):
            model_config = ConfigDict(defer_build=True, extra='allow')

            __pydantic_extra__: 'dict[str, int]'

    module_2 = create_module(
        f"""
from pydantic import BaseModel

from {module_1.__name__} import Bar

class Foo(BaseModel):
    bar: Bar
        """
    )

    extras_schema = module_2.Foo.__pydantic_core_schema__['schema']['fields']['bar']['schema']['schema'][
        'extras_schema'
    ]

    assert extras_schema == {'type': 'int'}


@pytest.mark.xfail(
    reason='While `get_cls_type_hints` uses the correct module ns for each base, `collect_model_fields` '
    'will still use the `FieldInfo` instances from each base (see the `parent_fields_lookup` logic). '
    'This means that `f` is still a forward ref in `Foo.model_fields`, and it gets evaluated in '
    '`GenerateSchema._model_schema`, where only the module of `Foo` is considered.'
)
def test_uses_the_correct_globals_to_resolve_model_forward_refs(create_module):
    @create_module
    def module_1():
        from pydantic import BaseModel

        class Bar(BaseModel):
            f: 'A'

        A = int

    module_2 = create_module(
        f"""
from {module_1.__name__} import Bar

A = str

class Foo(Bar):
    pass
        """
    )

    assert module_2.Foo.model_fields['f'].annotation is int


@pytest.mark.xfail(
    reason='We should keep a reference to the parent frame, not `f_locals`. '
    "It's probably only reasonable to support this in Python 3.14 with PEP 649."
)
def test_can_resolve_forward_refs_in_parent_frame_after_class_definition():
    def func():
        class Model(BaseModel):
            a: 'A'

        class A(BaseModel):
            pass

        return Model

    Model = func()

    Model.model_rebuild()


def test_uses_correct_global_ns_for_type_defined_in_separate_module(create_module):
    @create_module
    def module_1():
        from dataclasses import dataclass

        @dataclass
        class Bar:
            f: 'A'

        A = int

    module_2 = create_module(
        f"""
from pydantic import BaseModel
from {module_1.__name__} import Bar

A = str

class Foo(BaseModel):
    bar: Bar
        """
    )

    module_2.Foo(bar={'f': 1})


def test_uses_the_local_namespace_when_generating_schema():
    def func():
        A = int

        class Model(BaseModel):
            __pydantic_extra__: 'dict[str, A]'

            model_config = {'defer_build': True, 'extra': 'allow'}

        return Model

    Model = func()

    A = str  # noqa: F841

    Model.model_rebuild()
    Model(extra_value=1)


def test_uses_the_correct_globals_to_resolve_dataclass_forward_refs(create_module):
    @create_module
    def module_1():
        from dataclasses import dataclass

        A = int

        @dataclass
        class DC1:
            a: 'A'

    module_2 = create_module(f"""
from dataclasses import dataclass

from pydantic import BaseModel

from {module_1.__name__} import DC1

A = str

@dataclass
class DC2(DC1):
    b: 'A'

class Model(BaseModel):
    dc: DC2
    """)

    Model = module_2.Model

    Model(dc=dict(a=1, b='not_an_int'))


@pytest.mark.skipif(sys.version_info < (3, 12), reason='Requires PEP 695 syntax')
def test_class_locals_are_kept_during_schema_generation(create_module):
    create_module(
        """
from pydantic import BaseModel

class Model(BaseModel):
    type Test = int
    a: 'Test | Forward'

Forward = str

Model.model_rebuild()
        """
    )


def test_validate_call_does_not_override_the_global_ns_with_the_local_ns_where_it_is_used(create_module):
    from pydantic import validate_call

    @create_module
    def module_1():
        A = int

        def func(a: 'A'):
            pass

    def inner():
        A = str  # noqa: F841

        from module_1 import func

        func_val = validate_call(func)

        func_val(a=1)


def test_uses_the_correct_globals_to_resolve_forward_refs_on_serializers(create_module):
    # Note: unlike `test_uses_the_correct_globals_to_resolve_model_forward_refs`,
    # we use the globals of the underlying func to resolve the return type.
    @create_module
    def module_1():
        from typing import Annotated

        from pydantic import (
            BaseModel,
            PlainSerializer,  # or WrapSerializer
            field_serializer,  # or model_serializer, computed_field
        )

        MyStr = str

        def ser_func(value) -> 'MyStr':
            return str(value)

        class Model(BaseModel):
            a: int
            b: Annotated[int, PlainSerializer(ser_func)]

            @field_serializer('a')
            def ser(self, value) -> 'MyStr':
                return str(self.a)

    class Sub(module_1.Model):
        pass

    Sub.model_rebuild()


@pytest.mark.xfail(reason='parent namespace is used for every type in `NsResolver`, for backwards compatibility.')
def test_do_not_use_parent_ns_when_outside_the_function(create_module):
    @create_module
    def module_1():
        import dataclasses

        from pydantic import BaseModel

        @dataclasses.dataclass
        class A:
            a: 'Model'  # shouldn't resolve
            b: 'Test'  # same

        def inner():
            Test = int  # noqa: F841

            class Model(BaseModel, A):
                pass

            return Model

        ReturnedModel = inner()  # noqa: F841

    assert module_1.ReturnedModel.__pydantic_complete__ is False


# Tests related to forward annotations evaluation coupled with PEP 695 generic syntax:


@pytest.mark.skipif(sys.version_info < (3, 12), reason='Test related to PEP 695 syntax.')
def test_pep695_generics_syntax_base_model(create_module) -> None:
    mod_1 = create_module(
        """
from pydantic import BaseModel

class Model[T](BaseModel):
    t: 'T'
        """
    )

    assert mod_1.Model[int].model_fields['t'].annotation is int


@pytest.mark.skipif(sys.version_info < (3, 12), reason='Test related to PEP 695 syntax.')
def test_pep695_generics_syntax_arbitry_class(create_module) -> None:
    mod_1 = create_module(
        """
from typing import TypedDict

class TD[T](TypedDict):
    t: 'T'
        """
    )

    with pytest.raises(ValidationError):
        TypeAdapter(mod_1.TD[str]).validate_python({'t': 1})


@pytest.mark.skipif(sys.version_info < (3, 12), reason='Test related to PEP 695 syntax.')
def test_pep695_generics_class_locals_take_priority(create_module) -> None:
    # As per https://github.com/python/cpython/pull/120272
    mod_1 = create_module(
        """
from pydantic import BaseModel

class Model[T](BaseModel):
    type T = int
    t: 'T'
        """
    )

    # 'T' should resolve to the `TypeAliasType` instance, not the type variable:
    assert mod_1.Model[int].model_fields['t'].annotation.__value__ is int


@pytest.mark.skipif(sys.version_info < (3, 12), reason='Test related to PEP 695 syntax.')
def test_annotation_scope_skipped(create_module) -> None:
    # Documentation:
    # https://docs.python.org/3/reference/executionmodel.html#annotation-scopes
    # https://docs.python.org/3/reference/compound_stmts.html#generic-classes
    # Under the hood, `parent_frame_namespace` skips the annotation scope so that
    # we still properly fetch the namespace of `func` containing `Alias`.
    mod_1 = create_module(
        """
from pydantic import BaseModel

def func() -> None:
    Alias = int

    class Model[T](BaseModel):
        a: 'Alias'

    return Model

Model = func()
        """
    )

    assert mod_1.Model.model_fields['a'].annotation is int
