import pytest

from pydantic import BaseModel, ValidationError


class UltraSimpleModel(BaseModel):
    a: float = ...
    b: int = 10


def test_ultra_simple_success():
    m = UltraSimpleModel(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


def test_ultra_simple_failed():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert exc_info.value.args[0] == '1 errors validating input: {"a": {"msg": "field required", "type": "Missing"}}'


def test_ultra_simple_repr():
    m = UltraSimpleModel(a=10.2)
    assert repr(m) == '<UltraSimpleModel a=10.2 b=10>'


class ConfigModel(UltraSimpleModel):
    class Config:
        raise_exception = False


def test_config_doesnt_raise():
    m = ConfigModel()
    print(m.errors)
