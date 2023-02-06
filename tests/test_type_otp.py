import random

import pytest
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, Field
from pydantic.types import OTP, OTP_ALPHABET


# Test From Example
class TestGenerateOTP(BaseModel):
    """
    Generate an OTP
    """

    length: int = Field(6, ge=6, le=6)
    alphabet: str = Field(OTP_ALPHABET, min_length=6, max_length=32)

    def generate(self) -> OTP:
        return OTP(''.join(random.choices(self.alphabet, k=self.length)))


def test_otp_from_example():
    # Test successful validation
    valid_otp = TestGenerateOTP().generate()
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
    assert str(excinfo.value) == 'OTP must be 6 digits'
