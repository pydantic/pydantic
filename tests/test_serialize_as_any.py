import json
from dataclasses import dataclass
from typing import List, Optional

import pytest
from typing_extensions import TypedDict

from pydantic import BaseModel, RootModel, SecretStr, SerializeAsAny, TypeAdapter
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
