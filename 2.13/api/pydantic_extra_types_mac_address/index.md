The MAC address module provides functionality to parse and validate MAC addresses in different formats, such as IEEE 802 MAC-48, EUI-48, EUI-64, or a 20-octet format.

## MacAddress

Bases: `str`

Represents a MAC address and provides methods for conversion, validation, and serialization.

```py
from pydantic import BaseModel

from pydantic_extra_types.mac_address import MacAddress


class Network(BaseModel):
    mac_address: MacAddress


network = Network(mac_address='00:00:5e:00:53:01')
print(network)
# > mac_address='00:00:5e:00:53:01'

```

### validate_mac_address

```python
validate_mac_address(value: bytes) -> str

```

Validate a MAC Address from the provided byte value.

Source code in `pydantic_extra_types/mac_address.py`

```python
@staticmethod
def validate_mac_address(value: bytes) -> str:
    """Validate a MAC Address from the provided byte value."""
    raw = value.decode()
    if len(raw) < MINIMUM_LENGTH:
        raise PydanticCustomError(
            'mac_address_len',
            'Length for a {mac_address} MAC address must be {required_length}',
            {'mac_address': raw, 'required_length': MINIMUM_LENGTH},
        )

    for seperator, chunk_len in ((':', 2), ('-', 2), ('.', 4)):
        if seperator not in raw:
            continue

        parts = raw.split(seperator)
        if any(len(p) != chunk_len for p in parts):
            raise PydanticCustomError(
                'mac_address_format',
                f'Must have the format xx{seperator}xx{seperator}xx{seperator}xx{seperator}xx{seperator}xx',
            )

        total_bytes = (len(parts) * chunk_len) // 2
        if total_bytes not in ALLOWED_CHUNK_COUNTS:
            raise PydanticCustomError(
                'mac_address_format',
                'Length for a {mac_address} MAC address must be {required_length}',
                {'mac_address': raw, 'required_length': ALLOWED_CHUNK_COUNTS},
            )

        try:
            mac_bytes: list[int] = []
            for part in parts:
                for i in range(0, chunk_len, 2):
                    mac_bytes.append(int(part[i : i + 2], base=16))
        except ValueError as exc:
            raise PydanticCustomError('mac_address_format', 'Unrecognized format') from exc

        return ':'.join(f'{b:02x}' for b in mac_bytes)

    raise PydanticCustomError('mac_address_format', 'Unrecognized format')

```
