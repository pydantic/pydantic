import uuid
from decimal import Decimal
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from uuid import UUID

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    BaseModel,
    DirectoryPath,
    EmailStr,
    FilePath,
    IPvAnyAddress,
    IPvAnyInterface,
    IPvAnyNetwork,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    PositiveFloat,
    PositiveInt,
    PyObject,
    SecretBytes,
    SecretStr,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    constr,
)


class Model(BaseModel):
    cos_function: PyObject = None

    path_to_something: Path = None
    path_to_file: FilePath = None
    path_to_directory: DirectoryPath = None

    short_bytes: conbytes(min_length=2, max_length=10) = None
    strip_bytes: conbytes(strip_whitespace=True)

    short_str: constr(min_length=2, max_length=10) = None
    regex_str: constr(regex='apple (pie|tart|sandwich)') = None
    strip_str: constr(strip_whitespace=True)

    big_int: conint(gt=1000, lt=1024) = None
    mod_int: conint(multiple_of=5) = None
    pos_int: PositiveInt = None
    neg_int: NegativeInt = None

    big_float: confloat(gt=1000, lt=1024) = None
    unit_interval: confloat(ge=0, le=1) = None
    mod_float: confloat(multiple_of=0.5) = None
    pos_float: PositiveFloat = None
    neg_float: NegativeFloat = None

    short_list: conlist(int, min_items=1, max_items=4)

    email_address: EmailStr = None
    email_and_name: NameEmail = None

    password: SecretStr = None
    password_bytes: SecretBytes = None

    decimal: Decimal = None
    decimal_positive: condecimal(gt=0) = None
    decimal_negative: condecimal(lt=0) = None
    decimal_max_digits_and_places: condecimal(max_digits=2, decimal_places=2) = None
    mod_decimal: condecimal(multiple_of=Decimal('0.25')) = None
    uuid_any: UUID = None
    uuid_v1: UUID1 = None
    uuid_v3: UUID3 = None
    uuid_v4: UUID4 = None
    uuid_v5: UUID5 = None
    ipvany: IPvAnyAddress = None
    ipv4: IPv4Address = None
    ipv6: IPv6Address = None
    ip_vany_network: IPvAnyNetwork = None
    ip_v4_network: IPv4Network = None
    ip_v6_network: IPv6Network = None
    ip_vany_interface: IPvAnyInterface = None
    ip_v4_interface: IPv4Interface = None
    ip_v6_interface: IPv6Interface = None


m = Model(
    cos_function='math.cos',
    path_to_something='/home',
    path_to_file='docs/examples/example1.py',
    path_to_directory='docs/examples',
    short_bytes=b'foo',
    strip_bytes=b'   bar',
    short_str='foo',
    regex_str='apple pie',
    strip_str='   bar',
    big_int=1001,
    mod_int=155,
    pos_int=1,
    neg_int=-1,
    big_float=1002.1,
    mod_float=1.5,
    pos_float=2.2,
    neg_float=-2.3,
    unit_interval=0.5,
    short_list=[1, 2],
    email_address='Samuel Colvin <s@muelcolvin.com >',
    email_and_name='Samuel Colvin <s@muelcolvin.com >',
    password='password',
    password_bytes=b'password2',
    decimal=Decimal('42.24'),
    decimal_positive=Decimal('21.12'),
    decimal_negative=Decimal('-21.12'),
    decimal_max_digits_and_places=Decimal('0.99'),
    mod_decimal=Decimal('2.75'),
    uuid_any=uuid.uuid4(),
    uuid_v1=uuid.uuid1(),
    uuid_v3=uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org'),
    uuid_v4=uuid.uuid4(),
    uuid_v5=uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org'),
    ipvany=IPv4Address('192.168.0.1'),
    ipv4=IPv4Address('255.255.255.255'),
    ipv6=IPv6Address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'),
    ip_vany_network=IPv4Network('192.168.0.0/24'),
    ip_v4_network=IPv4Network('192.168.0.0/24'),
    ip_v6_network=IPv6Network('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'),
    ip_vany_interface=IPv4Interface('192.168.0.0/24'),
    ip_v4_interface=IPv4Interface('192.168.0.0/24'),
    ip_v6_interface=IPv6Interface('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'),
)
print(m.dict())
"""
{
    'cos_function': <built-in function cos>,
    'path_to_something': PosixPath('/home'),
    'path_to_file': PosixPath('/home/file.py'),
    'path_to_directory': PosixPath('/home/projects'),
    'short_bytes': b'foo',
    'strip_bytes': b'bar',
    'short_str': 'foo',
    'regex_str': 'apple pie',
    'strip_str': 'bar',
    'big_int': 1001,
    'mod_int': 155,
    'pos_int': 1,
    'neg_int': -1,
    'big_float': 1002.1,
    'mod_float': 1.5,
    'pos_float': 2.2,
    'neg_float': -2.3,
    'unit_interval': 0.5,
    'short_list': [1, 2],
    'email_address': 's@muelcolvin.com',
    'email_and_name': <NameEmail("Samuel Colvin <s@muelcolvin.com>")>,
    'is_really_a_bool': True,
    'password': SecretStr('**********'),
    'password_bytes': SecretBytes(b'**********'),
    ...
    'decimal': Decimal('42.24'),
    'decimal_positive': Decimal('21.12'),
    'decimal_negative': Decimal('-21.12'),
    'decimal_max_digits_and_places': Decimal('0.99'),
    'mod_decimal': Decimal('2.75'),
    'uuid_any': UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'),
    'uuid_v1': UUID('c96e505c-4c62-11e8-a27c-dca90496b483'),
    'uuid_v3': UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e'),
    'uuid_v4': UUID('22209f7a-aad1-491c-bb83-ea19b906d210'),
    'uuid_v5': UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d'),
    'ipvany': IPv4Address('192.168.0.1'),
    'ipv4': IPv4Address('255.255.255.255'),
    'ipv6': IPv6Address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'),
    'ip_vany_network': IPv4Network('192.168.0.0/24'),
    'ip_v4_network': IPv4Network('192.168.0.0/24'),
    'ip_v6_network': IPv4Network('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'),
    'ip_vany_interface': IPv4Interface('192.168.0.0/24'),
    'ip_v4_interface': IPv4Interface('192.168.0.0/24'),
    'ip_v6_interface': IPv6Interface('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
}
"""
