import json
from typing import List, Optional

from pydantic import BaseModel, SecretStr, SerializeAsAny


def test_serialize_as_any() -> None:
    class User(BaseModel):
        name: str

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        maybe_as_any: Optional[SerializeAsAny[User]] = None
        as_any: SerializeAsAny[User]
        without: User

    user = UserLogin(name='pydantic', password='password')

    # insert_assert(json.loads(OuterModel(as_any=user, without=user).model_dump_json()))
    assert json.loads(OuterModel(maybe_as_any=user, as_any=user, without=user).model_dump_json()) == {
        'maybe_as_any': {'name': 'pydantic', 'password': '**********'},
        'as_any': {'name': 'pydantic', 'password': '**********'},
        'without': {'name': 'pydantic'},
    }


def test_serialize_as_any_runtime() -> None:
    class User(BaseModel):
        name: str

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

    user = UserLogin(name='pydantic', password='password')
    assert json.loads(OuterModel(user=user).model_dump_json(serialize_as_any=True)) == {
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
    assert json.loads(OuterModel(user=user).model_dump_json(serialize_as_any=True)) == {
        'user': {
            'name': 'pydantic',
            'password': '**********',
            'friends': [{'name': 'pydantic', 'password': '**********', 'friends': []}],
        },
    }
