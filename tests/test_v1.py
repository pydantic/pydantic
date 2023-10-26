from pydantic import VERSION
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
