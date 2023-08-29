---
description: Support for storing data in an encoded form.
---

`EncodedBytes`
: a bytes value which is decoded from/encoded into a (different) bytes value during validation/serialization

`EncodedStr`
: a string value which is decoded from/encoded into a (different) string value during validation/serialization

`EncodedBytes` and `EncodedStr` needs an encoder that implements `EncoderProtocol` to operate.

```py
from typing import Optional

from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    EncodedBytes,
    EncodedStr,
    EncoderProtocol,
    ValidationError,
)


class MyEncoder(EncoderProtocol):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        if data == b'**undecodable**':
            raise ValueError('Cannot decode data')
        return data[13:]

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return b'**encoded**: ' + value

    @classmethod
    def get_json_format(cls) -> str:
        return 'my-encoder'


MyEncodedBytes = Annotated[bytes, EncodedBytes(encoder=MyEncoder)]
MyEncodedStr = Annotated[str, EncodedStr(encoder=MyEncoder)]


class Model(BaseModel):
    my_encoded_bytes: MyEncodedBytes
    my_encoded_str: Optional[MyEncodedStr] = None


# Initialize the model with encoded data
m = Model(
    my_encoded_bytes=b'**encoded**: some bytes',
    my_encoded_str='**encoded**: some str',
)

# Access decoded value
print(m.my_encoded_bytes)
#> b'some bytes'
print(m.my_encoded_str)
#> some str

# Serialize into the encoded form
print(m.model_dump())
"""
{
    'my_encoded_bytes': b'**encoded**: some bytes',
    'my_encoded_str': '**encoded**: some str',
}
"""

# Validate encoded data
try:
    Model(my_encoded_bytes=b'**undecodable**')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    my_encoded_bytes
      Value error, Cannot decode data [type=value_error, input_value=b'**undecodable**', input_type=bytes]
    """
```

## Base64 encoding support

Internally, Pydantic uses the [`EncodedBytes`][pydantic.types.EncodedBytes] and [`EncodedStr`][pydantic.types.EncodedStr]
annotations with [`Base64Encoder`][pydantic.types.Base64Encoder] to implement base64 encoding/decoding in the
[`Base64Bytes`][pydantic.types.Base64Bytes], [`Base64UrlBytes`][pydantic.types.Base64UrlBytes],
[`Base64Str`][pydantic.types.Base64Str], and [`Base64UrlStr`][pydantic.types.Base64Str] types.

```py
from typing import Optional

from pydantic import Base64Bytes, Base64Str, BaseModel, ValidationError


class Model(BaseModel):
    base64_bytes: Base64Bytes
    base64_str: Optional[Base64Str] = None


# Initialize the model with base64 data
m = Model(
    base64_bytes=b'VGhpcyBpcyB0aGUgd2F5',
    base64_str='VGhlc2UgYXJlbid0IHRoZSBkcm9pZHMgeW91J3JlIGxvb2tpbmcgZm9y',
)

# Access decoded value
print(m.base64_bytes)
#> b'This is the way'
print(m.base64_str)
#> These aren't the droids you're looking for

# Serialize into the base64 form
print(m.model_dump())
"""
{
    'base64_bytes': b'VGhpcyBpcyB0aGUgd2F5\n',
    'base64_str': 'VGhlc2UgYXJlbid0IHRoZSBkcm9pZHMgeW91J3JlIGxvb2tpbmcgZm9y\n',
}
"""

# Validate base64 data
try:
    print(Model(base64_bytes=b'undecodable').base64_bytes)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    base64_bytes
      Base64 decoding error: 'Incorrect padding' [type=base64_decode, input_value=b'undecodable', input_type=bytes]
    """
```

If you need url-safe base64 encoding, you can use the `Base64UrlBytes` and `Base64UrlStr` types. The following snippet
demonstrates the difference in alphabets used by the url-safe and non-url-safe encodings:

```py
from pydantic import (
    Base64Bytes,
    Base64Str,
    Base64UrlBytes,
    Base64UrlStr,
    BaseModel,
)


class Model(BaseModel):
    base64_bytes: Base64Bytes
    base64_str: Base64Str
    base64url_bytes: Base64UrlBytes
    base64url_str: Base64UrlStr


# Initialize the model with base64 data
m = Model(
    base64_bytes=b'SHc/dHc+TXc==',
    base64_str='SHc/dHc+TXc==',
    base64url_bytes=b'SHc_dHc-TXc==',
    base64url_str='SHc_dHc-TXc==',
)
print(m)
"""
base64_bytes=b'Hw?tw>Mw' base64_str='Hw?tw>Mw' base64url_bytes=b'Hw?tw>Mw' base64url_str='Hw?tw>Mw'
"""
```

!!! note
    Under the hood, `Base64Bytes` and `Base64Str` use the standard library `base64.encodebytes` and `base64.decodebytes`
    functions, while `Base64UrlBytes` and `Base64UrlStr` use the `base64.urlsafe_b64encode` and
    `base64.urlsafe_b64decode` functions.

    As a result, the `Base64UrlBytes` and `Base64UrlStr` types can be used to faithfully decode "vanilla" base64 data
    (using `'+'` and `'/'`), but the reverse is not true — attempting to decode url-safe base64 data using the
    `Base64Bytes` and `Base64Str` types may fail or produce an incorrect decoding.
