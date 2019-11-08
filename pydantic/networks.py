import re
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
    _BaseAddress,
    _BaseNetwork,
)
from typing import TYPE_CHECKING, Any, Dict, Generator, Optional, Set, Tuple, Type, Union, cast, no_type_check

from . import errors
from .utils import Representation
from .validators import constr_length_validator, str_validator

if TYPE_CHECKING:
    from .fields import ModelField
    from .main import BaseConfig  # noqa: F401
    from .typing import AnyCallable

    CallableGenerator = Generator[AnyCallable, None, None]

try:
    import email_validator
except ImportError:
    email_validator = None

NetworkType = Union[str, bytes, int, Tuple[Union[str, bytes, int], Union[str, int]]]

__all__ = [
    'AnyUrl',
    'AnyHttpUrl',
    'HttpUrl',
    'stricturl',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'RedisDsn',
    'validate_email',
]

host_part_names = ('domain', 'ipv4', 'ipv6')
url_regex = re.compile(
    r'(?:(?P<scheme>[a-z0-9]+?)://)?'  # scheme
    r'(?:(?P<user>[^\s:]+)(?::(?P<password>\S*))?@)?'  # user info
    r'(?:'
    r'(?P<ipv4>(?:\d{1,3}\.){3}\d{1,3})|'  # ipv4
    r'(?P<ipv6>\[[A-F0-9]*:[A-F0-9:]+\])|'  # ipv6
    r'(?P<domain>[^\s/:?#]+)'  # domain, validation occurs later
    r')?'
    r'(?::(?P<port>\d+))?'  # port
    r'(?P<path>/[^\s?]*)?'  # path
    r'(?:\?(?P<query>[^\s#]+))?'  # query
    r'(?:#(?P<fragment>\S+))?',  # fragment
    re.IGNORECASE,
)
_ascii_chunk = r'[_0-9a-z](?:[-_0-9a-z]{0,61}[_0-9a-z])?'
_domain_ending = r'(?P<tld>\.[a-z]{2,63})?\.?'
ascii_domain_regex = re.compile(fr'(?:{_ascii_chunk}\.)*?{_ascii_chunk}{_domain_ending}', re.IGNORECASE)

_int_chunk = r'[_0-9a-\U00040000](?:[-_0-9a-\U00040000]{0,61}[_0-9a-\U00040000])?'
int_domain_regex = re.compile(fr'(?:{_int_chunk}\.)*?{_int_chunk}{_domain_ending}', re.IGNORECASE)


class AnyUrl(str):
    strip_whitespace = True
    min_length = 1
    max_length = 2 ** 16
    allowed_schemes: Optional[Set[str]] = None
    tld_required: bool = False
    user_required: bool = False

    __slots__ = ('scheme', 'user', 'password', 'host', 'tld', 'host_type', 'port', 'path', 'query', 'fragment')

    @no_type_check
    def __new__(cls, url: Optional[str], **kwargs) -> object:
        return str.__new__(cls, cls.build(**kwargs) if url is None else url)

    def __init__(
        self,
        url: str,
        *,
        scheme: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str,
        tld: Optional[str] = None,
        host_type: str = 'domain',
        port: Optional[str] = None,
        path: Optional[str] = None,
        query: Optional[str] = None,
        fragment: Optional[str] = None,
    ) -> None:
        str.__init__(url)
        self.scheme = scheme
        self.user = user
        self.password = password
        self.host = host
        self.tld = tld
        self.host_type = host_type
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment

    @classmethod
    def build(
        cls,
        *,
        scheme: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str,
        port: Optional[str] = None,
        path: Optional[str] = None,
        query: Optional[str] = None,
        fragment: Optional[str] = None,
        **kwargs: str,
    ) -> str:
        url = scheme + '://'
        if user:
            url += user
            if password:
                url += ':' + password
            url += '@'
        url += host
        if port:
            url += ':' + port
        if path:
            url += path
        if query:
            url += '?' + query
        if fragment:
            url += '#' + fragment
        return url

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: 'ModelField', config: 'BaseConfig') -> 'AnyUrl':
        if type(value) == cls:
            return value
        value = str_validator(value)
        if cls.strip_whitespace:
            value = value.strip()
        url: str = cast(str, constr_length_validator(value, field, config))

        m = url_regex.match(url)
        # the regex should always match, if it doesn't please report with details of the URL tried
        assert m, 'URL regex failed unexpectedly'

        parts = m.groupdict()
        scheme = parts['scheme']
        if scheme is None:
            raise errors.UrlSchemeError()
        if cls.allowed_schemes and scheme.lower() not in cls.allowed_schemes:
            raise errors.UrlSchemePermittedError(cls.allowed_schemes)

        user = parts['user']
        if cls.user_required and user is None:
            raise errors.UrlUserInfoError()

        host, tld, host_type, rebuild = cls.validate_host(parts)

        if m.end() != len(url):
            raise errors.UrlExtraError(extra=url[m.end() :])

        return cls(
            None if rebuild else url,
            scheme=scheme,
            user=user,
            password=parts['password'],
            host=host,
            tld=tld,
            host_type=host_type,
            port=parts['port'],
            path=parts['path'],
            query=parts['query'],
            fragment=parts['fragment'],
        )

    @classmethod
    def validate_host(cls, parts: Dict[str, str]) -> Tuple[str, Optional[str], str, bool]:
        host, tld, host_type, rebuild = None, None, None, False
        for f in ('domain', 'ipv4', 'ipv6'):
            host = parts[f]
            if host:
                host_type = f
                break

        if host is None:
            raise errors.UrlHostError()
        elif host_type == 'domain':
            d = ascii_domain_regex.fullmatch(host)
            if d is None:
                d = int_domain_regex.fullmatch(host)
                if not d:
                    raise errors.UrlHostError()
                host_type = 'int_domain'
                rebuild = True
                host = host.encode('idna').decode('ascii')

            tld = d.group('tld')
            if tld is not None:
                tld = tld[1:]
            elif cls.tld_required:
                raise errors.UrlHostTldError()
        return host, tld, host_type, rebuild  # type: ignore

    def __repr__(self) -> str:
        extra = ', '.join(f'{n}={getattr(self, n)!r}' for n in self.__slots__ if getattr(self, n) is not None)
        return f'{self.__class__.__name__}({super().__repr__()}, {extra})'


class AnyHttpUrl(AnyUrl):
    allowed_schemes = {'http', 'https'}


class HttpUrl(AnyUrl):
    allowed_schemes = {'http', 'https'}
    tld_required = True
    # https://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
    max_length = 2083


class PostgresDsn(AnyUrl):
    allowed_schemes = {'postgres', 'postgresql'}
    user_required = True


class RedisDsn(AnyUrl):
    allowed_schemes = {'redis'}
    user_required = True


def stricturl(
    *,
    strip_whitespace: bool = True,
    min_length: int = 1,
    max_length: int = 2 ** 16,
    tld_required: bool = True,
    allowed_schemes: Optional[Set[str]] = None,
) -> Type[AnyUrl]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        tld_required=tld_required,
        allowed_schemes=allowed_schemes,
    )
    return type('UrlValue', (AnyUrl,), namespace)


class EmailStr(str):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        # included here and below so the error happens straight away
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        return validate_email(value)[1]


class NameEmail(Representation):
    __slots__ = 'name', 'email'

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> 'NameEmail':
        return cls(*validate_email(value))

    def __str__(self) -> str:
        return f'{self.name} <{self.email}>'


class IPvAnyAddress(_BaseAddress):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, bytes, int]) -> Union[IPv4Address, IPv6Address]:
        try:
            return IPv4Address(value)
        except ValueError:
            pass

        try:
            return IPv6Address(value)
        except ValueError:
            raise errors.IPvAnyAddressError()


class IPvAnyInterface(_BaseAddress):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: NetworkType) -> Union[IPv4Interface, IPv6Interface]:
        try:
            return IPv4Interface(value)
        except ValueError:
            pass

        try:
            return IPv6Interface(value)
        except ValueError:
            raise errors.IPvAnyInterfaceError()


class IPvAnyNetwork(_BaseNetwork):  # type: ignore
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: NetworkType) -> Union[IPv4Network, IPv6Network]:
        # Assume IP Network is defined with a default value for ``strict`` argument.
        # Define your own class if you want to specify network address check strictness.
        try:
            return IPv4Network(value)
        except ValueError:
            pass

        try:
            return IPv6Network(value)
        except ValueError:
            raise errors.IPvAnyNetworkError()


pretty_email_regex = re.compile(r'([\w ]*?) *<(.*)> *')


def validate_email(value: str) -> Tuple[str, str]:
    """
    Brutally simple email address validation. Note unlike most email address validation
    * raw ip address (literal) domain parts are not allowed.
    * "John Doe <local_part@domain.com>" style "pretty" email addresses are processed
    * the local part check is extremely basic. This raises the possibility of unicode spoofing, but no better
        solution is really possible.
    * spaces are striped from the beginning and end of addresses but no error is raised

    See RFC 5322 but treat it with suspicion, there seems to exist no universally acknowledged test for a valid email!
    """
    if email_validator is None:
        raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')

    m = pretty_email_regex.fullmatch(value)
    name: Optional[str] = None
    if m:
        name, value = m.groups()

    email = value.strip()

    try:
        email_validator.validate_email(email, check_deliverability=False)
    except email_validator.EmailNotValidError as e:
        raise errors.EmailError() from e

    at_index = email.index('@')
    local_part = email[:at_index]  # RFC 5321, local part must be case-sensitive.
    global_part = email[at_index:].lower()

    return name or local_part, local_part + global_part
