from ipaddress import IPv4Address, IPv6Address

import pytest

from pydantic import BaseModel, IPvAnyAddress, ValidationError


@pytest.mark.parametrize(
    'value,cls',
    [
        ('0.0.0.0', IPv4Address),
        ('1.1.1.1', IPv4Address),
        ('10.10.10.10', IPv4Address),
        ('192.168.0.1', IPv4Address),
        ('255.255.255.255', IPv4Address),
        ('::1:0:1', IPv6Address),
        ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff', IPv6Address),
        (b'\x00\x00\x00\x00', IPv4Address),
        (b'\x01\x01\x01\x01', IPv4Address),
        (b'\n\n\n\n', IPv4Address),
        (b'\xc0\xa8\x00\x01', IPv4Address),
        (b'\xff\xff\xff\xff', IPv4Address),
        (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01', IPv6Address),
        (b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Address),
        (0, IPv4Address),
        (16_843_009, IPv4Address),
        (168_430_090, IPv4Address),
        (3_232_235_521, IPv4Address),
        (4_294_967_295, IPv4Address),
        (4_294_967_297, IPv6Address),
        (340_282_366_920_938_463_463_374_607_431_768_211_455, IPv6Address),
        (IPv4Address('192.168.0.1'), IPv4Address),
        (IPv6Address('::1:0:1'), IPv6Address),
    ],
)
def test_ipaddress_success(value, cls):
    class Model(BaseModel):
        ip: IPvAnyAddress

    assert Model(ip=value).ip == cls(value)


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

    assert Model(ipv4=value).ipv4 == IPv4Address(value)


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

    assert Model(ipv6=value).ipv6 == IPv6Address(value)


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            'hello,world',
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipvanyaddress'}],
        ),
        (
            '192.168.0.1.1.1',
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipvanyaddress'}],
        ),
        (
            -1,
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipvanyaddress'}],
        ),
        (
            2 ** 128 + 1,
            [{'loc': ('ip',), 'msg': 'value is not a valid IPv4 or IPv6 address', 'type': 'value_error.ipvanyaddress'}],
        ),
    ],
)
def test_ipaddress_fails(value, errors):
    class Model(BaseModel):
        ip: IPvAnyAddress

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
        (
            IPv6Address('::0:1:0'),
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
        (
            IPv4Address('192.168.0.1'),
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
