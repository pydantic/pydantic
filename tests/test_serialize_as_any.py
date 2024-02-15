import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, SecretStr, SerializeAsAny


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


def test_serialize_as_any_on_config() -> None:
    class User(BaseModel):
        name: str

        model_config = ConfigDict(serialize_as_any=True)

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

    user = UserLogin(name='pydantic', password='password')
    assert OuterModel(user=user).model_dump() == {'user': {'name': 'pydantic', 'password': '**********'}}


def test_serialize_as_any_on_config_not_recursive() -> None:
    class User(BaseModel):
        name: str

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

        model_config = ConfigDict(serialize_as_any=True)

    user = UserLogin(name='pydantic', password='password')
    assert OuterModel(user=user).model_dump() == {'user': {'name': 'pydantic'}}


def test_serialize_as_any_runtime() -> None:
    class User(BaseModel):
        name: str

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

    user = UserLogin(name='pydantic', password='password')
    assert OuterModel(user=user).model_dump(serialize_as_any=True) == {
        'user': {'name': 'pydantic', 'password': '**********'}
    }


def test_serialize_as_any_runtime_recursive() -> None:
    class User(BaseModel):
        name: str

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

    user = UserLogin(name='pydantic', password='password')
    assert OuterModel(user=user).model_dump(serialize_as_any=True) == {
        'user': {'name': 'pydantic', 'password': '**********'}
    }


def test_serialize_as_any_on_config_priority() -> None:
    class User(BaseModel):
        name: str

        model_config = ConfigDict(serialize_as_any=False)

    class UserLogin(User):
        password: SecretStr

    class OuterModel(BaseModel):
        user: User

    user = UserLogin(name='pydantic', password='password')
    assert OuterModel(user=user).model_dump(serialize_as_any=True) == {'user': {'name': 'pydantic'}}
