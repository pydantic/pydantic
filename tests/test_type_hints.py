"""
Test pydantic model type hints (annotations) and that they can be
queried by :py:meth:`typing.get_type_hints`.
"""

import inspect
import sys
from typing import (
    Any,
    Dict,
    Generic,
    Optional,
    Set,
    TypeVar,
)

import pytest
import typing_extensions

from pydantic import (
    BaseModel,
    RootModel,
)
from pydantic.dataclasses import dataclass

DEPRECATED_MODEL_MEMBERS = {
    'construct',
    'copy',
    'dict',
    'from_orm',
    'json',
    'json_schema',
    'parse_file',
    'parse_obj',
}

# Disable deprecation warnings, as we enumerate members that may be
# i.e. pydantic.warnings.PydanticDeprecatedSince20: The `__fields__` attribute is deprecated,
#      use `model_fields` instead.
# Additionally, only run these tests for 3.10+
pytestmark = [
    pytest.mark.filterwarnings('ignore::DeprecationWarning'),
    pytest.mark.skipif(sys.version_info < (3, 10), reason='requires python3.10 or higher to work properly'),
]


@pytest.fixture(name='ParentModel', scope='session')
def parent_sub_model_fixture():
    class UltraSimpleModel(BaseModel):
        a: float
        b: int = 10

    class ParentModel(BaseModel):
        grape: bool
        banana: UltraSimpleModel

    return ParentModel


def inspect_type_hints(
    obj_type, members: Optional[Set[str]] = None, exclude_members: Optional[Set[str]] = None, recursion_limit: int = 3
):
    """
    Test an object and its members to make sure type hints can be resolved.
    :param obj_type: Type to check
    :param members: Explicit set of members to check, None to check all
    :param exclude_members: Set of member names to exclude
    :param recursion_limit: Recursion limit (0 to disallow)
    """

    try:
        hints = typing_extensions.get_type_hints(obj_type)
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
            if (members and member_name not in members) or (exclude_members and member_name in exclude_members):
                continue

            if inspect.isclass(member_obj) or inspect.isfunction(member_obj):
                # Inspect all child members (can't exclude specific ones)
                inspect_type_hints(member_obj, recursion_limit=recursion_limit - 1)


@pytest.mark.parametrize(
    ('obj_type', 'members', 'exclude_members'),
    [
        (BaseModel, None, DEPRECATED_MODEL_MEMBERS),
        (RootModel, None, DEPRECATED_MODEL_MEMBERS),
    ],
)
def test_obj_type_hints(obj_type, members: Optional[Set[str]], exclude_members: Optional[Set[str]]):
    """
    Test an object and its members to make sure type hints can be resolved.
    :param obj_type: Type to check
    :param members: Explicit set of members to check, None to check all
    :param exclude_members: Set of member names to exclude
    """
    inspect_type_hints(obj_type, members, exclude_members)


def test_parent_sub_model(ParentModel):
    inspect_type_hints(ParentModel, None, DEPRECATED_MODEL_MEMBERS)


def test_root_model_as_field():
    class MyRootModel(RootModel[int]):
        pass

    class MyModel(BaseModel):
        root_model: MyRootModel

    inspect_type_hints(MyRootModel, None, DEPRECATED_MODEL_MEMBERS)
    inspect_type_hints(MyModel, None, DEPRECATED_MODEL_MEMBERS)


def test_generics():
    data_type = TypeVar('data_type')

    class Result(BaseModel, Generic[data_type]):
        data: data_type

    inspect_type_hints(Result, None, DEPRECATED_MODEL_MEMBERS)
    inspect_type_hints(Result[Dict[str, Any]], None, DEPRECATED_MODEL_MEMBERS)


def test_dataclasses():
    @dataclass
    class MyDataclass:
        a: int
        b: float

    inspect_type_hints(MyDataclass)
