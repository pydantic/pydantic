import pickle
from typing import Annotated

import pytest
import typing_extensions
from annotated_types import Ge
from pydantic_core import MISSING, PydanticSerializationUnexpectedValue

from pydantic import BaseModel, TypeAdapter, ValidationError


def test_missing_sentinel_model() -> None:
    class Model(BaseModel):
        f: int | MISSING = MISSING
        g: MISSING = MISSING

    m1 = Model()

    assert m1.model_dump() == {}
    assert m1.model_dump_json() == '{}'

    m2 = Model.model_validate({'f': MISSING, 'g': MISSING})

    assert m2.f is MISSING
    assert m2.g is MISSING

    m3 = Model(f=1)

    assert m3.model_dump() == {'f': 1}
    assert m3.model_dump_json() == '{"f":1}'


def test_missing_sentinel_type_adapter() -> None:
    """Note that this usage isn't explicitly supported (and useless in practice)."""

    # TODO Remove annotation with PEP 747:
    ta: TypeAdapter[object] = TypeAdapter(MISSING)

    assert ta.validate_python(MISSING) is MISSING

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1)

    assert exc_info.value.errors()[0]['type'] == 'missing_sentinel_error'

    assert ta.dump_python(MISSING) is MISSING

    with pytest.raises(PydanticSerializationUnexpectedValue):
        ta.dump_python(1)


# Defined in module to be picklable:
class ModelPickle(BaseModel):
    f: int | MISSING = MISSING


@pytest.mark.xfail(
    # Unreleased typing-extensions has the final sentinel implementation with pickle support:
    condition=not hasattr(typing_extensions, 'sentinel'),
    reason="PEP 661 sentinels aren't picklable yet in the experimental typing-extensions implementation",
)
def test_missing_sentinel_pickle() -> None:
    m = ModelPickle()
    m_reconstructed = pickle.loads(pickle.dumps(m))

    assert m_reconstructed.f is MISSING


def test_missing_sentinel_json_schema() -> None:
    class Model(BaseModel):
        f: int | MISSING = MISSING
        g: MISSING = MISSING
        h: MISSING

    assert Model.model_json_schema()['properties'] == {
        'f': {'title': 'F', 'type': 'integer'},
    }


def test_model_construct_with_missing_default_does_not_crash() -> None:
    class M(BaseModel):
        a: int | MISSING = MISSING

    # Should not raise
    m = M.model_construct()
    assert hasattr(m, 'a')
    # Keep sentinel by identity
    assert getattr(m, 'a') is MISSING


def test_no_warning_when_excluded_in_nested_model() -> None:
    """https://github.com/pydantic/pydantic/issues/12628"""

    class Inner(BaseModel):
        f1: int | MISSING = MISSING
        f2: int | MISSING = MISSING

    class Outer(BaseModel):
        inner: Inner | MISSING = MISSING

    s = Outer(
        inner={'f1': 1},
    )

    # Shouldn't raise a serialization warning about missing fields:
    assert s.model_dump() == {'inner': {'f1': 1}}


def test_missing_sentinel_constraints_pushdown() -> None:
    class Model(BaseModel):
        f1: Annotated[int | MISSING, Ge(1)] = MISSING
        f2: Annotated[MISSING | int, Ge(1)] = MISSING
        f3: Annotated[int | str | MISSING, Ge(1)] = MISSING
        f4: Annotated[int | str | None | MISSING, Ge(1)] = MISSING

    js_schema = Model.model_json_schema()

    assert js_schema['properties']['f1'] == {'minimum': 1, 'title': 'F1', 'type': 'integer'}
    assert js_schema['properties']['f2'] == {'minimum': 1, 'title': 'F2', 'type': 'integer'}
    # Note: 'ge' is still wrong (see https://github.com/pydantic/pydantic/issues/11576)
    assert js_schema['properties']['f3'] == {'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'ge': 1, 'title': 'F3'}
    assert js_schema['properties']['f4'] == {
        'anyOf': [{'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'ge': 1}, {'type': 'null'}],
        'title': 'F4',
    }


def test_missing_sentinel_child_fields() -> None:
    """https://github.com/pydantic/pydantic/issues/13001."""

    class Base(BaseModel, extra='forbid'):
        base_field: str | MISSING = MISSING

    class Parent(Base):
        parent_field: str

    class Child(Parent):
        child_field: str

    class Container(BaseModel, extra='forbid'):
        item: Parent | MISSING = MISSING

    child = Child(parent_field='p', child_field='c')
    container = Container(item=child)

    result = TypeAdapter(Container).dump_python(container)

    assert result == {'item': {'parent_field': 'p'}}
