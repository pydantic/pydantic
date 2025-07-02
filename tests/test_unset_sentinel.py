import pickle

import pytest
from pydantic_core import UNSET, PydanticSerializationUnexpectedValue

from pydantic import BaseModel, TypeAdapter, ValidationError


def test_unset_sentinel_model() -> None:
    class Model(BaseModel):
        f: int | UNSET = UNSET
        g: UNSET = UNSET

    m1 = Model()

    assert m1.model_dump() == {}
    assert m1.model_dump_json() == '{}'

    m2 = Model.model_validate({'f': UNSET, 'g': UNSET})

    assert m2.f is UNSET
    assert m2.g is UNSET

    m3 = Model(f=1)

    assert m3.model_dump() == {'f': 1}
    assert m3.model_dump_json() == '{"f": 1}'


def test_unset_sentinel_type_adapter() -> None:
    """Note that this usage isn't explicitly supported (and useless in practice)."""

    # TODO Remove annotation with PEP 747:
    ta: TypeAdapter[object] = TypeAdapter(UNSET)

    assert ta.validate_python(UNSET) is UNSET

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1)

    assert exc_info.value.errors()[0]['type'] == 'unset_sentinel_error'

    assert ta.dump_python(UNSET) is UNSET

    with pytest.raises(PydanticSerializationUnexpectedValue):
        ta.dump_python(1)


# Defined in module to be picklable:
class ModelPickle(BaseModel):
    f: int | UNSET = UNSET


def test_unset_sentinel_pickle() -> None:
    m = ModelPickle()
    m_reconstructed = pickle.loads(pickle.dumps(m))

    assert m_reconstructed.f is UNSET


def test_unset_sentinel_json_schema() -> None:
    class Model(BaseModel):
        f: int | UNSET = UNSET
        g: UNSET = UNSET
        h: UNSET

    assert Model.model_json_schema()['properties'] == {
        'f': {'title': 'F', 'type': 'integer'},
    }
