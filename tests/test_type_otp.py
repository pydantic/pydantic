import pytest
from pydantic_core import PydanticCustomError

from pydantic.types import OTP


def test_otp():
    # Test successful validation
    valid_otp = OTP.validate('123456')
    assert isinstance(valid_otp, OTP)

    # Test validation error for non-digit characters
    with pytest.raises(PydanticCustomError) as excinfo:
        OTP.validate('1A2345')
    assert str(excinfo.value) == 'OTP is not all digits'

    # Test validation error for length less than 6
    with pytest.raises(PydanticCustomError) as excinfo:
        OTP.validate('12345')
    assert str(excinfo.value) == 'OTP must be 6 digits'

    # Test validation error for length greater than 6
    with pytest.raises(PydanticCustomError) as excinfo:
        OTP.validate('1234567')
    assert str(excinfo.value) == 'OTP must be 6 digits'

    # Test validation error for empty string
    with pytest.raises(PydanticCustomError) as excinfo:
        OTP.validate('')
    assert str(excinfo.value) == 'OTP is not all digits'
