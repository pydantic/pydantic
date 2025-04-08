The MAC address module provides functionality to parse and validate MAC addresses in different formats, such as IEEE 802 MAC-48, EUI-48, EUI-64, or a 20-octet format.

## MacAddress

Bases: `str`

Represents a MAC address and provides methods for conversion, validation, and serialization.

```py
from pydantic import BaseModel

from pydantic_extra_types.mac_address import MacAddress


class Network(BaseModel):
    mac_address: MacAddress


network = Network(mac_address="00:00:5e:00:53:01")
print(network)
#> mac_address='00:00:5e:00:53:01'

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
    """
    Validate a MAC Address from the provided byte value.
    """
    if len(value) < 14:
        raise PydanticCustomError(
            'mac_address_len',
            'Length for a {mac_address} MAC address must be {required_length}',
            {'mac_address': value.decode(), 'required_length': 14},
        )

    if value[2] in [ord(':'), ord('-')]:
        if (len(value) + 1) % 3 != 0:
            raise PydanticCustomError(
                'mac_address_format', 'Must have the format xx:xx:xx:xx:xx:xx or xx-xx-xx-xx-xx-xx'
            )
        n = (len(value) + 1) // 3
        if n not in (6, 8, 20):
            raise PydanticCustomError(
                'mac_address_format',
                'Length for a {mac_address} MAC address must be {required_length}',
                {'mac_address': value.decode(), 'required_length': (6, 8, 20)},
            )
        mac_address = bytearray(n)
        x = 0
        for i in range(n):
            try:
                byte_value = int(value[x : x + 2], 16)
                mac_address[i] = byte_value
                x += 3
            except ValueError as e:
                raise PydanticCustomError('mac_address_format', 'Unrecognized format') from e

    elif value[4] == ord('.'):
        if (len(value) + 1) % 5 != 0:
            raise PydanticCustomError('mac_address_format', 'Must have the format xx.xx.xx.xx.xx.xx')
        n = 2 * (len(value) + 1) // 5
        if n not in (6, 8, 20):
            raise PydanticCustomError(
                'mac_address_format',
                'Length for a {mac_address} MAC address must be {required_length}',
                {'mac_address': value.decode(), 'required_length': (6, 8, 20)},
            )
        mac_address = bytearray(n)
        x = 0
        for i in range(0, n, 2):
            try:
                byte_value = int(value[x : x + 2], 16)
                mac_address[i] = byte_value
                byte_value = int(value[x + 2 : x + 4], 16)
                mac_address[i + 1] = byte_value
                x += 5
            except ValueError as e:
                raise PydanticCustomError('mac_address_format', 'Unrecognized format') from e

    else:
        raise PydanticCustomError('mac_address_format', 'Unrecognized format')

    return ':'.join(f'{b:02x}' for b in mac_address)

```
