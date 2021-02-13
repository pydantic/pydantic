import typing
from hypothesis import given, strategies as st
from pydantic import BaseModel, EmailStr, PaymentCardNumber, PositiveFloat


class Model(BaseModel):
    card: PaymentCardNumber
    price: PositiveFloat
    users: typing.List[EmailStr]


@given(st.builds(Model))
def test_property(instance):
    # Hypothesis calls this test function many times with varied Models,
    # so you can write a test that should pass given *any* instance.
    assert 0 < instance.price
    assert all('@' in email for email in instance.users)


@given(st.builds(Model, price=st.floats(100, 200)))
def test_with_discount(instance):
    # This test shows how you can override specific fields,
    # and let Hypothesis fill in any you don't care about.
    assert 100 <= instance.price <= 200
