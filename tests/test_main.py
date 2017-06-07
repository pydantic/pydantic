import json
from typing import Any

import pytest

from pydantic import BaseModel, ConfigError, NoneBytes, NoneStr, Required, ValidationError, pretty_errors


def test_success():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float
        b: int = 10

    m = Model(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


class UltraSimpleModel(BaseModel):
    a: float = ...
    b: int = 10


def test_ultra_simple_missing():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert """\
1 error validating input
a:
  field required (error_type=Missing)""" == str(exc_info.value)


def test_ultra_simple_failed():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel(a='x', b='x')
    assert """\
2 errors validating input
a:
  could not convert string to float: 'x' (error_type=ValueError track=float)
b:
  invalid literal for int() with base 10: 'x' (error_type=ValueError track=int)\
""" == str(exc_info.value)


def test_ultra_simple_repr():
    m = UltraSimpleModel(a=10.2)
    assert repr(m) == '<UltraSimpleModel a=10.2 b=10>'
    assert repr(m.fields['a']) == ("<Field a: type='float', required=True, "
                                   "validators=['float', 'number_size_validator']>")
    assert dict(m) == {'a': 10.2, 'b': 10}


def test_str_truncate():
    class Model(BaseModel):
        s1: str
        s2: str
        b1: bytes
        b2: bytes
    m = Model(s1='132', s2='x' * 100, b1='123', b2='x' * 100)
    print(repr(m.to_string()))
    assert m.to_string() == ("Model s1='132' "
                             "s2='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...' "
                             "b1=b'123' "
                             "b2=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...")
    assert """\
Model
  s1='132'
  s2='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'
  b1=b'123'
  b2=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...""" == m.to_string(pretty=True)


def test_comparing():
    m = UltraSimpleModel(a=10.2, b='100')
    assert m == {'a': 10.2, 'b': 100}
    assert m == UltraSimpleModel(a=10.2, b=100)


def test_nullable_strings_success():
    class NoneCheckModel(BaseModel):
        existing_str_value = 'foo'
        required_str_value: str = ...
        required_str_none_value: NoneStr = ...
        existing_bytes_value = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: NoneBytes = ...

    m = NoneCheckModel(
        required_str_value='v1',
        required_str_none_value=None,
        required_bytes_value='v2',
        required_bytes_none_value=None,
    )
    assert m.required_str_value == 'v1'
    assert m.required_str_none_value is None
    assert m.required_bytes_value == b'v2'
    assert m.required_bytes_none_value is None


def test_nullable_strings_fails():
    class NoneCheckModel(BaseModel):
        existing_str_value = 'foo'
        required_str_value: str = ...
        required_str_none_value: NoneStr = ...
        existing_bytes_value = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: NoneBytes = ...

    try:
        NoneCheckModel(
            required_str_value=None,
            required_str_none_value=None,
            required_bytes_value=None,
            required_bytes_none_value=None,
        )
    except ValidationError as e:
        assert """\
{
  "required_bytes_value": {
    "error_msg": "None is not an allow value",
    "error_type": "TypeError",
    "index": null,
    "track": "bytes"
  },
  "required_str_value": {
    "error_msg": "None is not an allow value",
    "error_type": "TypeError",
    "index": null,
    "track": "str"
  }
}""" == json.dumps(pretty_errors(e.errors_raw), indent=2, sort_keys=True)


class RecursiveModel(BaseModel):
    grape: bool = ...
    banana: UltraSimpleModel = ...


def test_recursion():
    m = RecursiveModel(grape=1, banana={'a': 1})
    assert m.grape is True
    assert m.banana.a == 1.0
    assert m.banana.b == 10
    assert repr(m) == '<RecursiveModel grape=True banana=<UltraSimpleModel a=1.0 b=10>>'


def test_recursion_fails():
    with pytest.raises(ValidationError):
        RecursiveModel(grape=1, banana=123)


class PreventExtraModel(BaseModel):
    foo = 'whatever'

    class Config:
        ignore_extra = False


def test_prevent_extra_success():
    m = PreventExtraModel()
    assert m.foo == 'whatever'
    m = PreventExtraModel(foo=1)
    assert m.foo == '1'


def test_prevent_extra_fails():
    with pytest.raises(ValidationError) as exc_info:
        PreventExtraModel(foo='ok', bar='wrong', spam='xx')
    assert exc_info.value.message == '2 errors validating input'
    assert """\
bar:
  extra fields not permitted (error_type=Extra)
spam:
  extra fields not permitted (error_type=Extra)""" == exc_info.value.display_errors


class InvalidValidator:
    @classmethod
    def get_validators(cls):
        yield cls.has_wrong_arguments

    @classmethod
    def has_wrong_arguments(cls, value, bar):
        pass


def test_invalid_validator():
    with pytest.raises(ConfigError) as exc_info:
        class InvalidValidatorModel(BaseModel):
            x: InvalidValidator = ...
    assert exc_info.value.args[0].startswith('Invalid signature for validator')


def test_no_validator():
    with pytest.raises(ConfigError) as exc_info:
        class NoValidatorModel(BaseModel):
            x: object = ...
    assert exc_info.value.args[0] == "no validator found for <class 'object'>"


def test_unable_to_infer():
    with pytest.raises(ConfigError) as exc_info:
        class InvalidDefinitionModel(BaseModel):
            x = None
    assert exc_info.value.args[0] == 'unable to infer type for attribute "x"'


def test_not_required():
    class Model(BaseModel):
        a: float = None
    assert Model(a=12.2).a == 12.2
    assert Model().a is None
    assert Model(a=None).a is None


def test_infer_type():
    class Model(BaseModel):
        a = False
        b = ''
        c = 0
    assert Model().a is False
    assert Model().b == ''
    assert Model().c == 0


def test_allow_extra():
    class Model(BaseModel):
        a: float = ...

        class Config:
            allow_extra = True

    assert Model(a='10.2', b=12).values() == {'a': 10.2, 'b': 12}


def test_set_attr():
    m = UltraSimpleModel(a=10.2)
    assert m.values() == {'a': 10.2, 'b': 10}
    m.b = 20
    assert m.values() == {'a': 10.2, 'b': 20}


def test_set_attr_invalid():

    class UltraSimpleModel(BaseModel):
        a: float = ...
        b: int = 10
    m = UltraSimpleModel(a=10.2)
    assert m.values() == {'a': 10.2, 'b': 10}
    with pytest.raises(ValueError) as exc_info:
        m.c = 20
    assert '"UltraSimpleModel" object has no field "c"' in str(exc_info)


def test_any():
    class AnyModel(BaseModel):
        a: Any = 10

    assert AnyModel().a == 10
    assert AnyModel(a='foobar').a == 'foobar'


def test_alias():
    class Model(BaseModel):
        a = 'foobar'

        class Config:
            fields = {
                'a': {'alias': '_a'}
            }

    assert Model().a == 'foobar'
    assert Model().values() == {'a': 'foobar'}
    assert Model(_a='different').a == 'different'
    assert Model(_a='different').values() == {'a': 'different'}


def test_field_order():
    class Model(BaseModel):
        c: float
        b: int = 10
        a: str
        d: dict = {}

    # fields are ordered as defined except annotation-only fields come last
    assert list(Model.__fields__.keys()) == ['b', 'd', 'c', 'a']


def test_required():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float = Required
        b: int = 10

    m = Model(a=10.2)
    assert m.values() == dict(a=10.2, b=10)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert """\
1 error validating input
a:
  field required (error_type=Missing)\
""" == str(exc_info.value)
