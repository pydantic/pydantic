import json
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any, List

import pytest

from pydantic import BaseModel, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork, ValidationError
from pydantic.config import ConfigDict


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
        IPv4Address('0.0.0.0'),
        IPv4Address('1.1.1.1'),
        IPv4Address('10.10.10.10'),
        IPv4Address('192.168.0.1'),
        IPv4Address('255.255.255.255'),
    ],
)
def test_ipv4address_success(value):
    class Model(BaseModel):
        ipv4: IPv4Address

    assert Model(ipv4=value).ipv4 == IPv4Address(value)


@pytest.mark.parametrize(
    'tp,value,errors',
    [
        (
            IPv4Address,
            IPv4Address('0.0.0.0'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv4Address',
                    'input': '0.0.0.0',
                    'ctx': {'class': 'IPv4Address'},
                }
            ],
        ),
        (
            IPv4Interface,
            IPv4Interface('192.168.0.0/24'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv4Interface',
                    'input': '192.168.0.0/24',
                    'ctx': {'class': 'IPv4Interface'},
                }
            ],
        ),
        (
            IPv4Network,
            IPv4Network('192.168.0.0/24'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv4Network',
                    'input': '192.168.0.0/24',
                    'ctx': {'class': 'IPv4Network'},
                }
            ],
        ),
        (
            IPv6Address,
            IPv6Address('::1:0:1'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv6Address',
                    'input': '::1:0:1',
                    'ctx': {'class': 'IPv6Address'},
                }
            ],
        ),
        (
            IPv6Interface,
            IPv6Interface('2001:db00::0/120'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv6Interface',
                    'input': '2001:db00::/120',
                    'ctx': {'class': 'IPv6Interface'},
                }
            ],
        ),
        (
            IPv6Network,
            IPv6Network('2001:db00::0/120'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv6Network',
                    'input': '2001:db00::/120',
                    'ctx': {'class': 'IPv6Network'},
                }
            ],
        ),
    ],
)
def test_ip_strict(tp: Any, value: Any, errors: List[Any]) -> None:
    class Model(BaseModel):
        v: tp

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=str(value))
    assert exc_info.value.errors(include_url=False) == errors

    assert Model(v=value).v == value


@pytest.mark.parametrize(
    'value',
    [
        '::1:0:1',
        'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01',
        b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff',
        4_294_967_297,
        340_282_366_920_938_463_463_374_607_431_768_211_455,
        IPv6Address('::1:0:1'),
        IPv6Address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'),
    ],
)
def test_ipv6address_success(value):
    class Model(BaseModel):
        ipv6: IPv6Address

    assert Model(ipv6=value).ipv6 == IPv6Address(value)


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1', -1, 2**128 + 1])
def test_ipaddress_fails(value):
    class Model(BaseModel):
        ip: IPvAnyAddress

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_any_address',
        'loc': ('ip',),
        'msg': 'value is not a valid IPv4 or IPv6 address',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1', -1, 2**32 + 1, IPv6Address('::0:1:0')])
def test_ipv4address_fails(value):
    class Model(BaseModel):
        ipv4: IPv4Address

    with pytest.raises(ValidationError) as exc_info:
        Model(ipv4=value)
    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v4_address',
        'loc': ('ipv4',),
        'msg': 'Input is not a valid IPv4 address',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1', -1, 2**128 + 1, IPv4Address('192.168.0.1')])
def test_ipv6address_fails(value):
    class Model(BaseModel):
        ipv6: IPv6Address

    with pytest.raises(ValidationError) as exc_info:
        Model(ipv6=value)
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v6_address',
        'loc': ('ipv6',),
        'msg': 'Input is not a valid IPv6 address',
        'input': value,
    }


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Network),
        ('192.168.128.0/30', IPv4Network),
        ('2001:db00::0/120', IPv6Network),
        (2**32 - 1, IPv4Network),  # no mask equals to mask /32
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Network),  # /128
        (b'\xff\xff\xff\xff', IPv4Network),  # /32
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Network),
        (('192.168.0.0', 24), IPv4Network),
        (('2001:db00::0', 120), IPv6Network),
        (IPv4Network('192.168.0.0/24'), IPv4Network),
    ],
)
def test_ipnetwork_success(value, cls):
    class Model(BaseModel):
        ip: IPvAnyNetwork = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Network),
        ('192.168.128.0/30', IPv4Network),
        (2**32 - 1, IPv4Network),  # no mask equals to mask /32
        (b'\xff\xff\xff\xff', IPv4Network),  # /32
        (('192.168.0.0', 24), IPv4Network),
        (IPv4Network('192.168.0.0/24'), IPv4Network),
    ],
)
def test_ip_v4_network_success(value, cls):
    class Model(BaseModel):
        ip: IPv4Network = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('2001:db00::0/120', IPv6Network),
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Network),  # /128
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Network),
        (('2001:db00::0', 120), IPv6Network),
        (IPv6Network('2001:db00::0/120'), IPv6Network),
    ],
)
def test_ip_v6_network_success(value, cls):
    class Model(BaseModel):
        ip: IPv6Network = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ipnetwork_fails(value):
    class Model(BaseModel):
        ip: IPvAnyNetwork = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_any_network',
        'loc': ('ip',),
        'msg': 'value is not a valid IPv4 or IPv6 network',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1, '2001:db00::1/120'])
def test_ip_v4_network_fails(value):
    class Model(BaseModel):
        ip: IPv4Network = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v4_network',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv4 network',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1, '192.168.0.1/24'])
def test_ip_v6_network_fails(value):
    class Model(BaseModel):
        ip: IPv6Network = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v6_network',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv6 network',
        'input': value,
    }


def test_ipvany_serialization():
    class Model(BaseModel):
        address: IPvAnyAddress
        network: IPvAnyNetwork
        interface: IPvAnyInterface

    m = Model(address='127.0.0.1', network='192.0.2.0/27', interface='127.0.0.1/32')
    assert json.loads(m.model_dump_json()) == {
        'address': '127.0.0.1',
        'interface': '127.0.0.1/32',
        'network': '192.0.2.0/27',
    }


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Interface),
        ('192.168.0.1/24', IPv4Interface),
        ('192.168.128.0/30', IPv4Interface),
        ('192.168.128.1/30', IPv4Interface),
        ('2001:db00::0/120', IPv6Interface),
        ('2001:db00::1/120', IPv6Interface),
        (2**32 - 1, IPv4Interface),  # no mask equals to mask /32
        (2**32 - 1, IPv4Interface),  # so `strict` has no effect
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Interface),  # /128
        (20_282_409_603_651_670_423_947_251_286_014, IPv6Interface),
        (b'\xff\xff\xff\xff', IPv4Interface),  # /32
        (b'\xff\xff\xff\xff', IPv4Interface),
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Interface),
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Interface),
        (('192.168.0.0', 24), IPv4Interface),
        (('192.168.0.1', 24), IPv4Interface),
        (('2001:db00::0', 120), IPv6Interface),
        (('2001:db00::1', 120), IPv6Interface),
        (IPv4Interface('192.168.0.0/24'), IPv4Interface),
        (IPv4Interface('192.168.0.1/24'), IPv4Interface),
        (IPv6Interface('2001:db00::0/120'), IPv6Interface),
        (IPv6Interface('2001:db00::1/120'), IPv6Interface),
    ],
)
def test_ipinterface_success(value, cls):
    class Model(BaseModel):
        ip: IPvAnyInterface = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Interface),
        ('192.168.0.1/24', IPv4Interface),
        ('192.168.128.0/30', IPv4Interface),
        ('192.168.128.1/30', IPv4Interface),
        (2**32 - 1, IPv4Interface),  # no mask equals to mask /32
        (2**32 - 1, IPv4Interface),  # so `strict` has no effect
        (b'\xff\xff\xff\xff', IPv4Interface),  # /32
        (b'\xff\xff\xff\xff', IPv4Interface),
        (('192.168.0.0', 24), IPv4Interface),
        (('192.168.0.1', 24), IPv4Interface),
        (IPv4Interface('192.168.0.0/24'), IPv4Interface),
        (IPv4Interface('192.168.0.1/24'), IPv4Interface),
    ],
)
def test_ip_v4_interface_success(value, cls):
    class Model(BaseModel):
        ip: IPv4Interface

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('2001:db00::0/120', IPv6Interface),
        ('2001:db00::1/120', IPv6Interface),
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Interface),  # /128
        (20_282_409_603_651_670_423_947_251_286_014, IPv6Interface),
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Interface),
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Interface),
        (('2001:db00::0', 120), IPv6Interface),
        (('2001:db00::1', 120), IPv6Interface),
        (IPv6Interface('2001:db00::0/120'), IPv6Interface),
        (IPv6Interface('2001:db00::1/120'), IPv6Interface),
    ],
)
def test_ip_v6_interface_success(value, cls):
    class Model(BaseModel):
        ip: IPv6Interface = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ipinterface_fails(value):
    class Model(BaseModel):
        ip: IPvAnyInterface = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_any_interface',
        'loc': ('ip',),
        'msg': 'value is not a valid IPv4 or IPv6 interface',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ip_v4_interface_fails(value):
    class Model(BaseModel):
        ip: IPv4Interface = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v4_interface',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv4 interface',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ip_v6_interface_fails(value):
    class Model(BaseModel):
        ip: IPv6Interface = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v6_interface',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv6 interface',
        'input': value,
    }
