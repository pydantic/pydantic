import warnings

from pydantic import VERSION
from pydantic import BaseModel as V2BaseModel
from pydantic.v1 import VERSION as V1_VERSION
from pydantic.v1 import BaseModel as V1BaseModel
from pydantic.v1 import root_validator as v1_root_validator


def test_version():
    assert V1_VERSION.startswith('1.')
    assert V1_VERSION != VERSION


def test_root_validator():
    class Model(V1BaseModel):
        v: str

        @v1_root_validator(pre=True)
        @classmethod
        def root_validator(cls, values):
            values['v'] += '-v1'
            return values

    model = Model(v='value')
    assert model.v == 'value-v1'


def test_isinstance_does_not_raise_deprecation_warnings():
    class V1Model(V1BaseModel):
        v: int

    class V2Model(V2BaseModel):
        v: int

    v1_obj = V1Model(v=1)
    v2_obj = V2Model(v=2)

    with warnings.catch_warnings():
        warnings.simplefilter('error')

        assert isinstance(v1_obj, V1BaseModel)
        assert not isinstance(v1_obj, V2BaseModel)
        assert not isinstance(v2_obj, V1BaseModel)
        assert isinstance(v2_obj, V2BaseModel)
