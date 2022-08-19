import typing
from datetime import date

import pytest

import pydantic
from pydantic.networks import import_email_validator

try:
    from hypothesis import HealthCheck, given, settings, strategies as st
except ImportError:
    from unittest import mock

    given = settings = lambda *a, **kw: (lambda f: f)  # pass-through decorator
    HealthCheck = st = mock.Mock()

    pytestmark = pytest.mark.skipif(True, reason='"hypothesis" not installed')


def gen_models():
    class MiscModel(pydantic.BaseModel):
        # Each of these models contains a few related fields; the idea is that
        # if there's a bug we have neither too many fields to dig through nor
        # too many models to read.
        obj: pydantic.PyObject
        color: pydantic.color.Color
        json_any: pydantic.Json

    class StringsModel(pydantic.BaseModel):
        card: pydantic.PaymentCardNumber
        secbytes: pydantic.SecretBytes
        secstr: pydantic.SecretStr

    class UUIDsModel(pydantic.BaseModel):
        uuid1: pydantic.UUID1
        uuid3: pydantic.UUID3
        uuid4: pydantic.UUID4
        uuid5: pydantic.UUID5

    class IPvAnyAddress(pydantic.BaseModel):
        address: pydantic.IPvAnyAddress

    class IPvAnyInterface(pydantic.BaseModel):
        interface: pydantic.IPvAnyInterface

    class IPvAnyNetwork(pydantic.BaseModel):
        network: pydantic.IPvAnyNetwork

    class StrictNumbersModel(pydantic.BaseModel):
        strictbool: pydantic.StrictBool
        strictint: pydantic.StrictInt
        strictfloat: pydantic.StrictFloat
        strictstr: pydantic.StrictStr

    class NumbersModel(pydantic.BaseModel):
        posint: pydantic.PositiveInt
        negint: pydantic.NegativeInt
        posfloat: pydantic.PositiveFloat
        negfloat: pydantic.NegativeFloat
        nonposint: pydantic.NonPositiveInt
        nonnegint: pydantic.NonNegativeInt
        nonposfloat: pydantic.NonPositiveFloat
        nonnegfloat: pydantic.NonNegativeFloat

    class JsonModel(pydantic.BaseModel):
        json_int: pydantic.Json[int]
        json_float: pydantic.Json[float]
        json_str: pydantic.Json[str]
        json_int_or_str: pydantic.Json[typing.Union[int, str]]
        json_list_of_float: pydantic.Json[typing.List[float]]
        json_pydantic_model: pydantic.Json[pydantic.BaseModel]

    class ConstrainedNumbersModel(pydantic.BaseModel):
        conintt: pydantic.conint(gt=10, lt=100)
        coninte: pydantic.conint(ge=10, le=100)
        conintmul: pydantic.conint(ge=10, le=100, multiple_of=7)
        confloatt: pydantic.confloat(gt=10, lt=100)
        confloate: pydantic.confloat(ge=10, le=100)
        confloatemul: pydantic.confloat(ge=10, le=100, multiple_of=4.2)
        confloattmul: pydantic.confloat(gt=10, lt=100, multiple_of=10)
        condecimalt: pydantic.condecimal(gt=10, lt=100)
        condecimale: pydantic.condecimal(ge=10, le=100)
        condecimaltplc: pydantic.condecimal(gt=10, lt=100, decimal_places=5)
        condecimaleplc: pydantic.condecimal(ge=10, le=100, decimal_places=2)

    class ConstrainedDateModel(pydantic.BaseModel):
        condatet: pydantic.condate(gt=date(1980, 1, 1), lt=date(2180, 12, 31))
        condatee: pydantic.condate(ge=date(1980, 1, 1), le=date(2180, 12, 31))

    yield from (
        MiscModel,
        StringsModel,
        UUIDsModel,
        IPvAnyAddress,
        IPvAnyInterface,
        IPvAnyNetwork,
        StrictNumbersModel,
        NumbersModel,
        JsonModel,
        ConstrainedNumbersModel,
        ConstrainedDateModel,
    )

    try:
        import_email_validator()
    except ImportError:
        pass
    else:

        class EmailsModel(pydantic.BaseModel):
            email: pydantic.EmailStr
            name_email: pydantic.NameEmail

        yield EmailsModel


@pytest.mark.parametrize('model', gen_models())
@settings(suppress_health_check={HealthCheck.too_slow}, deadline=None)
@given(data=st.data())
def test_can_construct_models_with_all_fields(data, model):
    # The value of this test is to confirm that Hypothesis knows how to provide
    # valid values for each field - otherwise, this would raise ValidationError.
    instance = data.draw(st.from_type(model))

    # We additionally check that the instance really is of type `model`, because
    # an evil implementation could avoid ValidationError by means of e.g.
    # `st.register_type_strategy(model, st.none())`, skipping the constructor.
    assert isinstance(instance, model)
