import json
from dataclasses import dataclass
from typing import List, Optional

import pytest
from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, RootModel, SecretStr, SerializeAsAny, TypeAdapter
from pydantic.dataclasses import dataclass as pydantic_dataclass


class User(BaseModel):
    name: str


class UserLogin(User):
    password: SecretStr


user = User(name='pydantic')
user_login = UserLogin(name='pydantic', password='password')


def test_serialize_as_any_annotation() -> None:
    class OuterModel(BaseModel):
        maybe_as_any: Optional[SerializeAsAny[User]] = None
        as_any: SerializeAsAny[User]
        without: User

    # insert_assert(json.loads(OuterModel(as_any=user, without=user).model_dump_json()))
    assert json.loads(OuterModel(maybe_as_any=user_login, as_any=user_login, without=user_login).model_dump_json()) == {
        'maybe_as_any': {'name': 'pydantic', 'password': '**********'},
        'as_any': {'name': 'pydantic', 'password': '**********'},
        'without': {'name': 'pydantic'},
    }


def test_serialize_as_any_runtime() -> None:
    class OuterModel(BaseModel):
        user: User

    assert json.loads(OuterModel(user=user_login).model_dump_json(serialize_as_any=False)) == {
        'user': {'name': 'pydantic'}
    }
    assert json.loads(OuterModel(user=user_login).model_dump_json(serialize_as_any=True)) == {
        'user': {'name': 'pydantic', 'password': '**********'}
    }


def test_serialize_as_any_runtime_recursive() -> None:
    class User(BaseModel):
        name: str
        friends: List['User']

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

    user = UserLogin(
        name='pydantic', password='password', friends=[UserLogin(name='pydantic', password='password', friends=[])]
    )

    assert json.loads(OuterModel(user=user).model_dump_json(serialize_as_any=False)) == {
        'user': {
            'name': 'pydantic',
            'friends': [{'name': 'pydantic', 'friends': []}],
        },
    }
    assert json.loads(OuterModel(user=user).model_dump_json(serialize_as_any=True)) == {
        'user': {
            'name': 'pydantic',
            'password': '**********',
            'friends': [{'name': 'pydantic', 'password': '**********', 'friends': []}],
        },
    }


def test_serialize_as_any_with_rootmodel() -> None:
    UserRoot = RootModel[User]
    assert json.loads(UserRoot(root=user_login).model_dump_json(serialize_as_any=False)) == {'name': 'pydantic'}
    assert json.loads(UserRoot(root=user_login).model_dump_json(serialize_as_any=True)) == {
        'name': 'pydantic',
        'password': '**********',
    }


def test_serialize_as_any_type_adapter() -> None:
    ta = TypeAdapter(User)
    assert json.loads(ta.dump_json(user_login, serialize_as_any=False)) == {'name': 'pydantic'}
    assert json.loads(ta.dump_json(user_login, serialize_as_any=True)) == {'name': 'pydantic', 'password': '**********'}


@pytest.mark.parametrize('dataclass_constructor', [dataclass, pydantic_dataclass])
def test_serialize_as_any_with_dataclasses(dataclass_constructor) -> None:
    @dataclass_constructor
    class User:
        name: str

    @dataclass_constructor
    class UserLogin(User):
        password: str

    user_login = UserLogin(name='pydantic', password='password')

    ta = TypeAdapter(User)
    assert json.loads(ta.dump_json(user_login, serialize_as_any=False, warnings=False)) == {'name': 'pydantic'}
    assert json.loads(ta.dump_json(user_login, serialize_as_any=True, warnings=False)) == {
        'name': 'pydantic',
        'password': 'password',
    }


def test_serialize_as_any_with_typed_dict() -> None:
    class User(TypedDict):
        name: str

    class UserLogin(User):
        password: str

    user_login = UserLogin(name='pydantic', password='password')

    ta = TypeAdapter(User)
    assert json.loads(ta.dump_json(user_login, serialize_as_any=False, warnings=False)) == {'name': 'pydantic'}
    assert json.loads(ta.dump_json(user_login, serialize_as_any=True, warnings=False)) == {
        'name': 'pydantic',
        'password': 'password',
    }


def test_serialize_as_any_flag_on_unrelated_models() -> None:
    class Parent(BaseModel):
        x: int

    class Other(BaseModel):
        y: str

        model_config = ConfigDict(extra='allow')

    ta = TypeAdapter(Parent)
    other = Other(x=1, y='hello')
    assert ta.dump_python(other, serialize_as_any=False) == {}
    assert ta.dump_python(other, serialize_as_any=True) == {'y': 'hello', 'x': 1}


def test_serialize_as_any_annotation_on_unrelated_models() -> None:
    class Parent(BaseModel):
        x: int

    class Other(BaseModel):
        y: str

        model_config = ConfigDict(extra='allow')

    ta = TypeAdapter(Parent)
    other = Other(x=1, y='hello')
    assert ta.dump_python(other) == {}

    ta_any = TypeAdapter(SerializeAsAny[Parent])
    assert ta_any.dump_python(other) == {'y': 'hello', 'x': 1}


def test_serialize_as_any_with_inner_models() -> None:
    """As with other serialization flags, serialize_as_any affects nested models as well."""

    class Inner(BaseModel):
        x: int

    class Outer(BaseModel):
        inner: Inner

    class InnerChild(Inner):
        y: int

    ta = TypeAdapter(Outer)
    inner_child = InnerChild(x=1, y=2)
    outer = Outer(inner=inner_child)

    assert ta.dump_python(outer, serialize_as_any=False) == {'inner': {'x': 1}}
    assert ta.dump_python(outer, serialize_as_any=True) == {'inner': {'x': 1, 'y': 2}}


def test_serialize_as_any_annotation_with_inner_models() -> None:
    """The SerializeAsAny annotation does not affect nested models."""

    class Inner(BaseModel):
        x: int

    class Outer(BaseModel):
        inner: Inner

    class InnerChild(Inner):
        y: int

    ta = TypeAdapter(SerializeAsAny[Outer])
    inner_child = InnerChild(x=1, y=2)
    outer = Outer(inner=inner_child)
    assert ta.dump_python(outer) == {'inner': {'x': 1}}


def test_serialize_as_any_flag_with_incorrect_list_el_type() -> None:
    # a warning is raised when using the `serialize_as_any` flag
    ta = TypeAdapter(List[int])
    with pytest.warns(UserWarning, match='Expected `int` but got `str`'):
        assert ta.dump_python(['a', 'b', 'c'], serialize_as_any=False) == ['a', 'b', 'c']


def test_serialize_as_any_annotation_with_incorrect_list_el_type() -> None:
    # notably, the warning is not raised when using the SerializeAsAny annotation
    ta = TypeAdapter(SerializeAsAny[List[int]])
    assert ta.dump_python(['a', 'b', 'c']) == ['a', 'b', 'c']
