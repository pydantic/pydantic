import random

from pydantic import BaseModel, Field
from pydantic.types import OTP, OTP_ALPHABET


class GenerateOTP(BaseModel):
    """
    Generate an OTP
    """

    length: int = Field(6, ge=6, le=6)
    alphabet: str = Field(OTP_ALPHABET, min_length=6, max_length=32)

    def generate(self) -> OTP:
        return OTP(''.join(random.choices(self.alphabet, k=self.length)))

    def __str__(self) -> str:
        return self.generate()


otp = GenerateOTP()

assert otp.length == 6
assert otp.alphabet == OTP_ALPHABET