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
from typing import TYPE_CHECKING, Any, Generator, Optional, Set, Tuple, Type, Union, cast, no_type_check

from . import errors
from .utils import change_exception
from .validators import constr_length_validator, not_none_validator, str_validator

if TYPE_CHECKING:  # pragma: no cover
    from .fields import Field
    from .main import BaseConfig  # noqa: F401
    from .utils import AnyCallable

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
    'urlstr',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'RedisDsn',
    'validate_email',
]


class AnyUrl(str):
    strip_whitespace = True
    min_length = 1
    max_length = 2 ** 16
    allowed_schemes: Optional[Set[str]] = None
    tld_required: bool = False
    user_required: bool = False

    __slots__ = ('scheme', 'user', 'password', 'host', 'port', 'path', 'query', 'fragment')

    @no_type_check
    def __new__(cls, url: str, **kwargs: Optional[str]) -> object:
        return str.__new__(cls, url)

    def __init__(
        self,
        url: str,
        *,
        scheme: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str,
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
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield not_none_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: 'Field', config: 'BaseConfig') -> 'AnyUrl':
        if type(value) == cls:
            return value
        value = str_validator(value)
        if cls.strip_whitespace:
            value = value.strip()
        url: str = cast(str, constr_length_validator(value, field, config))

        m = url_regex.match(url)
        if not m:  # pragma: no cover
            # FIXME can this actually ever happen?
            raise errors.UrlError()

        parts = m.groupdict()
        # debug(parts)
        scheme = parts['scheme']
        if scheme is None:
            raise errors.UrlSchemeError()
        if cls.allowed_schemes and scheme.lower() not in cls.allowed_schemes:
            raise errors.UrlSchemePermittedError(cls.allowed_schemes)

        if cls.user_required and parts['user'] is None:
            raise errors.UrlUserInfoError()

        host = parts['host']
        if host is None:
            raise errors.UrlHostError()
        elif cls.tld_required and not host_tld_regex.fullmatch(host):
            raise errors.UrlHostTldError()

        if m.end() != len(url):
            raise errors.UrlExtraError(extra=url[m.end() :])

        return cls(url, **parts)

    @no_type_check
    def strip(self) -> str:
        # required so constr_length_validator doesn't simplify AnyStr objects to strings
        return self

    def __repr__(self) -> str:
        extra = ' '.join(f'{n}={getattr(self, n)!r}' for n in self.__slots__ if getattr(self, n) is not None)
        return f'<{type(self).__name__}({super().__repr__()} {extra})>'


class AnyHttpUrl(AnyUrl):
    allowed_schemes = {'http', 'https'}


class HttpUrl(AnyUrl):
    allowed_schemes = {'http', 'https'}
    tld_required = True


class PostgresDsn(AnyUrl):
    allowed_schemes = {'postgres', 'postgresql'}
    user_required = True


class RedisDsn(AnyUrl):
    allowed_schemes = {'redis'}
    user_required = True


def urlstr(
    *,
    strip_whitespace: bool = True,
    min_length: int = 1,
    max_length: int = 2 ** 16,
    tld_required: bool = True,
    allowed_schemes: Optional[Set[str]] = None,
) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        tld_required=tld_required,
        allowed_schemes=allowed_schemes,
    )
    return type('UrlStrValue', (AnyUrl,), namespace)


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


class NameEmail:
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

    def __repr__(self) -> str:
        return f'<NameEmail("{self}")>'


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

        with change_exception(errors.IPvAnyAddressError, ValueError):
            return IPv6Address(value)


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

        with change_exception(errors.IPvAnyInterfaceError, ValueError):
            return IPv6Interface(value)


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

        with change_exception(errors.IPvAnyNetworkError, ValueError):
            return IPv6Network(value)


def _host_regex_str(require_tld: bool = False) -> str:
    """
    Host regex generator.

    :param require_tld: whether the URL must include a top level domain, eg. reject non-FQDN hostnames
    """
    domain_chunk = r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?'
    domain = fr'(?:{domain_chunk}\.)*{domain_chunk}'
    if require_tld:
        domain += r'\.[a-z]{2,63}'
    host_options = (
        domain + r'\.?',
        r'localhost\.?',  # TODO is this required?
        r'(?:\d{1,3}\.){3}\d{1,3}',  # ipv4
        r'\[[A-F0-9]*:[A-F0-9:]+\]',  # ipv6
    )
    return r'(?P<host>' + '|'.join(host_options) + ')'


url_regex = re.compile(
    ''.join(
        f'(?:{r})?'
        for r in (
            r'(?P<scheme>[a-z0-9]+?)://',  # scheme
            r'(?P<user>\S+)(?P<password>:\S*)?@',  # user info
            _host_regex_str(False),  # host
            r':(?P<port>\d+)',  # port
            r'(?P<path>/[^\s\?]*)',  # path
            r'\?(?P<query>[^\s#]+)',  # query
            r'#(?P<fragment>\S+)',  # fragment
        )
    ),
    re.IGNORECASE,
)
host_tld_regex = re.compile(_host_regex_str(True), re.IGNORECASE)
PRETTY_EMAIL_REGEX = re.compile(r'([\w ]*?) *<(.*)> *')


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

    m = PRETTY_EMAIL_REGEX.fullmatch(value)
    name: Optional[str] = None
    if m:
        name, value = m.groups()

    email = value.strip()

    try:
        email_validator.validate_email(email, check_deliverability=False)
    except email_validator.EmailNotValidError as e:
        raise errors.EmailError() from e

    return name or email[: email.index('@')], email.lower()
