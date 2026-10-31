"""
Test pydantic model type hints (annotations) and that they can be
queried by :py:meth:`typing.get_type_hints`.
"""

import inspect
from functools import lru_cache
from typing import (
    Any,
    Generic,
    TypeVar,
)

import pytest
import typing_extensions

from pydantic import (
    BaseModel,
    RootModel,
)
from pydantic.dataclasses import dataclass


@pytest.fixture(name='ParentModel', scope='session')
def parent_sub_model_fixture():
    class UltraSimpleModel(BaseModel):
        a: float
        b: int = 10

    class ParentModel(BaseModel):
        grape: bool
        banana: UltraSimpleModel

    return ParentModel


@lru_cache
def get_type_checking_only_ns():
    """
    When creating `BaseModel` in `pydantic.main`, some globals are imported only when `TYPE_CHECKING` is `True`, so we have to manually include them when calling `typing.get_type_hints`.
    """

    from inspect import Signature

    from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator

    from pydantic.fields import ComputedFieldInfo, FieldInfo, ModelPrivateAttr
    from pydantic.fields import PrivateAttr as _PrivateAttr

    return {
        'Signature': Signature,
        'CoreSchema': CoreSchema,
        'SchemaSerializer': SchemaSerializer,
        'SchemaValidator': SchemaValidator,
        'ComputedFieldInfo': ComputedFieldInfo,
        'FieldInfo': FieldInfo,
        'ModelPrivateAttr': ModelPrivateAttr,
        '_PrivateAttr': _PrivateAttr,
    }


def inspect_type_hints(obj_type, members: set[str] | None = None, recursion_limit: int = 3):
    """
    Test an object and its members to make sure type hints can be resolved.
    :param obj_type: Type to check
    :param members: Explicit set of members to check, None to check all
    :param recursion_limit: Recursion limit (0 to disallow)
    """

    try:
        hints = typing_extensions.get_type_hints(obj_type, localns=get_type_checking_only_ns())
        assert isinstance(hints, dict), f'Type annotation(s) on {obj_type} are invalid'
    except NameError as ex:
        raise AssertionError(f'Type annotation(s) on {obj_type} are invalid: {str(ex)}') from ex

    if recursion_limit <= 0:
        return

    if isinstance(obj_type, type):
        # Check class members
        for member_name, member_obj in inspect.getmembers(obj_type):
            if member_name.startswith('_'):
                # Ignore private members
                continue
            if members and member_name not in members:
                continue

            if inspect.isclass(member_obj) or inspect.isfunction(member_obj):
                # Inspect all child members (can't exclude specific ones)
                inspect_type_hints(member_obj, recursion_limit=recursion_limit - 1)


@pytest.mark.parametrize(
    ('obj_type', 'members'),
    [
        (BaseModel, None),
        (RootModel, None),
    ],
)
def test_obj_type_hints(obj_type, members: set[str] | None):
    """
    Test an object and its members to make sure type hints can be resolved.
    :param obj_type: Type to check
    :param members: Explicit set of members to check, None to check all
    """
    inspect_type_hints(obj_type, members)


def test_parent_sub_model(ParentModel):
    inspect_type_hints(ParentModel)


def test_root_model_as_field():
    class MyRootModel(RootModel[int]):
        pass

    class MyModel(BaseModel):
        root_model: MyRootModel

    inspect_type_hints(MyRootModel)
    inspect_type_hints(MyModel)


def test_generics():
    data_type = TypeVar('data_type')

    class Result(BaseModel, Generic[data_type]):
        data: data_type

    inspect_type_hints(Result)
    inspect_type_hints(Result[dict[str, Any]])


def test_dataclasses():
    @dataclass
    class MyDataclass:
        a: int
        b: float

    inspect_type_hints(MyDataclass)
