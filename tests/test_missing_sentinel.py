import pickle
from typing import Union

import pytest
from pydantic_core import MISSING, PydanticSerializationUnexpectedValue

from pydantic import BaseModel, TypeAdapter, ValidationError


def test_missing_sentinel_model() -> None:
    class Model(BaseModel):
        f: Union[int, MISSING] = MISSING
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
    f: Union[int, MISSING] = MISSING


@pytest.mark.xfail(reason="PEP 661 sentinels aren't picklable yet in the experimental typing-extensions implementation")
def test_missing_sentinel_pickle() -> None:
    m = ModelPickle()
    m_reconstructed = pickle.loads(pickle.dumps(m))

    assert m_reconstructed.f is MISSING


def test_missing_sentinel_json_schema() -> None:
    class Model(BaseModel):
        f: Union[int, MISSING] = MISSING
        g: MISSING = MISSING
        h: MISSING

    assert Model.model_json_schema()['properties'] == {
        'f': {'title': 'F', 'type': 'integer'},
    }
