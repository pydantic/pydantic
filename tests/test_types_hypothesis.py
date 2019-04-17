from hypothesis import given, settings
from hypothesis import strategies as st

from pydantic.types import EmailStr


@given(t=st.just(EmailStr()), email=st.emails())
@settings(max_examples=10000000)
def test_email(t, email):
    """
    The
    address format is specified in :rfc:`5322#section-3.4.1`. Values shrink
    towards shorter local-parts and host domains.

    """
    t.validate(email)
