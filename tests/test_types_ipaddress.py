import ipaddress

import pytest

from pydantic import BaseModel, IPAddress, IPv4Address, IPv6Address, ValidationError


@pytest.mark.parametrize(
    'value',
    [
        '0.0.0.0',
        '1.1.1.1',
        '10.10.10.10',
        '192.168.0.1',
        '255.255.255.255',
        '::1:0:1',
        'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
    ],
)
def test_ipaddress_str_success(value):
    class Model(BaseModel):
        ip: IPAddress

    assert Model(ip=value).ip == value


@pytest.mark.parametrize(
    'value',
    [
        b'\x00\x00\x00\x00',
        b'\x01\x01\x01\x01',
        b'\n\n\n\n',
        b'\xc0\xa8\x00\x01',
        b'\xff\xff\xff\xff',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01',
        b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff',
    ],
)
def test_ipaddress_bytes_success(value):
    class Model(BaseModel):
        ip: IPAddress

    assert Model(ip=value).ip == str(ipaddress.ip_address(value))


@pytest.mark.parametrize(
    'value',
    [
        0,
        16_843_009,
        168_430_090,
        3_232_235_521,
        4_294_967_295,
        4_294_967_297,
        340_282_366_920_938_463_463_374_607_431_768_211_455,
    ],
)
def test_ipaddress_ints_success(value):
    class Model(BaseModel):
        ip: IPAddress

    assert Model(ip=value).ip == str(ipaddress.ip_address(value))


@pytest.mark.parametrize(
    'value',
    [
        '0.0.0.0',
        '1.1.1.1',
        '10.10.10.10',
        '192.168.0.1',
        '255.255.255.255',
        b'\x00\x00\x00\x00',
        b'\x01\x01\x01\x01',
        b'\n\n\n\n',
        b'\xc0\xa8\x00\x01',
        b'\xff\xff\xff\xff',
        0,
        16_843_009,
        168_430_090,
        3_232_235_521,
        4_294_967_295,
    ],
)
def test_ipv4address_success(value):
    class Model(BaseModel):
        ipv4: IPv4Address

    assert Model(ipv4=value).ipv4 == str(ipaddress.IPv4Address(value))


@pytest.mark.parametrize(
    'value',
    [
        '::1:0:1',
        'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01',
        b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff',
        4_294_967_297,
        340_282_366_920_938_463_463_374_607_431_768_211_455,
    ],
)
def test_ipv6address_success(value):
    class Model(BaseModel):
        ipv6: IPv6Address

    assert Model(ipv6=value).ipv6 == str(ipaddress.IPv6Address(value))


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            'hello,world',
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipaddress'}],
        ),
        (
            '192.168.0.1.1.1',
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipaddress'}],
        ),
        (-1, [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipaddress'}]),
        (
            2 ** 128 + 1,
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipaddress'}],
        ),
    ],
)
def test_ipaddress_fails(value, errors):
    class Model(BaseModel):
        ip: IPAddress

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            'hello,world',
            [{'loc': ('ipv4',), 'msg': 'value is not a valid IPv4 address', 'type': 'value_error.ipv4address'}],
        ),
        (
            '192.168.0.1.1.1',
            [{'loc': ('ipv4',), 'msg': 'value is not a valid IPv4 address', 'type': 'value_error.ipv4address'}],
        ),
        (-1, [{'loc': ('ipv4',), 'msg': 'value is not a valid IPv4 address', 'type': 'value_error.ipv4address'}]),
        (
            2 ** 32 + 1,
            [{'loc': ('ipv4',), 'msg': 'value is not a valid IPv4 address', 'type': 'value_error.ipv4address'}],
        ),
    ],
)
def test_ipv4address_fails(value, errors):
    class Model(BaseModel):
        ipv4: IPv4Address

    with pytest.raises(ValidationError) as exc_info:
        Model(ipv4=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            'hello,world',
            [{'loc': ('ipv6',), 'msg': 'value is not a valid IPv6 address', 'type': 'value_error.ipv6address'}],
        ),
        (
            '192.168.0.1.1.1',
            [{'loc': ('ipv6',), 'msg': 'value is not a valid IPv6 address', 'type': 'value_error.ipv6address'}],
        ),
        (-1, [{'loc': ('ipv6',), 'msg': 'value is not a valid IPv6 address', 'type': 'value_error.ipv6address'}]),
        (
            2 ** 128 + 1,
            [{'loc': ('ipv6',), 'msg': 'value is not a valid IPv6 address', 'type': 'value_error.ipv6address'}],
        ),
    ],
)
def test_ipv6address_fails(value, errors):
    class Model(BaseModel):
        ipv6: IPv6Address

    with pytest.raises(ValidationError) as exc_info:
        Model(ipv6=value)
    assert exc_info.value.errors() == errors
