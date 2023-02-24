import json
from typing import Mapping

from pydantic import BaseModel


class DataModel(BaseModel):
    data: str


class KeyModel(BaseModel):
    __root__: str

    class Config:
        allow_mutation = False
        frozen = True


class MapModel(BaseModel):
    __root__: Mapping[KeyModel, DataModel]


def test_json():
    mm = MapModel.parse_obj({KeyModel.parse_obj('test'): DataModel.parse_obj({'data': 'something'})})
    assert mm.json() == json.dumps({'test': {'data': 'something'}})
