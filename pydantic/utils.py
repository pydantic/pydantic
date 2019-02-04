import inspect
import re
import sys
from contextlib import contextmanager
from enum import Enum
from functools import lru_cache
from importlib import import_module
from textwrap import dedent
from typing import _eval_type  # type: ignore
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Pattern, Tuple, Type, Union

from . import errors

try:
    import email_validator
except ImportError:
    email_validator = None

try:
    from typing import _TypingBase as typing_base  # type: ignore
except ImportError:
    from typing import _Final as typing_base  # type: ignore

try:
    from typing import ForwardRef  # type: ignore
except ImportError:
    # python 3.6
    ForwardRef = None

if TYPE_CHECKING:  # pragma: no cover
    from .main import BaseModel  # noqa: F401

if sys.version_info < (3, 7):
    from typing import Callable

    AnyCallable = Callable[..., Any]
else:
    from collections.abc import Callable
    from typing import Callable as TypingCallable

    AnyCallable = TypingCallable[..., Any]


PRETTY_REGEX = re.compile(r'([\w ]*?) *<(.*)> *')
AnyType = Type[Any]


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

    m = PRETTY_REGEX.fullmatch(value)
    name: Optional[str] = None
    if m:
        name, value = m.groups()

    email = value.strip()

    try:
        email_validator.validate_email(email, check_deliverability=False)
    except email_validator.EmailNotValidError as e:
        raise errors.EmailError() from e

    return name or email[: email.index('@')], email.lower()


def _rfc_1738_quote(text: str) -> str:
    return re.sub(r'[:@/]', lambda m: '%{:X}'.format(ord(m.group(0))), text)


def make_dsn(
    *,
    driver: str,
    user: str = None,
    password: str = None,
    host: str = None,
    port: str = None,
    name: str = None,
    query: Dict[str, Any] = None,
) -> str:
    """
    Create a DSN from from connection settings.

    Stolen approximately from sqlalchemy/engine/url.py:URL.
    """
    s = driver + '://'
    if user is not None:
        s += _rfc_1738_quote(user)
        if password is not None:
            s += ':' + _rfc_1738_quote(password)
        s += '@'
    if host is not None:
        if ':' in host:
            s += '[{}]'.format(host)
        else:
            s += host
    if port is not None:
        s += ':{}'.format(int(port))
    if name is not None:
        s += '/' + name
    query = query or {}
    if query:
        keys = list(query)
        keys.sort()
        s += '?' + '&'.join('{}={}'.format(k, query[k]) for k in keys)
    return s


def import_string(dotted_path: str) -> Any:
    """
    Stolen approximately from django. Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails.
    """
    try:
        module_path, class_name = dotted_path.strip(' ').rsplit('.', 1)
    except ValueError as e:
        raise ImportError(f'"{dotted_path}" doesn\'t look like a module path') from e

    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute') from e


def truncate(v: str, *, max_len: int = 80) -> str:
    """
    Truncate a value and add a unicode ellipsis (three dots) to the end if it was too long
    """
    if isinstance(v, str) and len(v) > (max_len - 2):
        # -3 so quote + string + … + quote has correct length
        return repr(v[: (max_len - 3)] + '…')
    v = repr(v)
    if len(v) > max_len:
        v = v[: max_len - 1] + '…'
    return v


def display_as_type(v: AnyType) -> str:
    if not isinstance(v, typing_base) and not isinstance(v, type):
        v = type(v)

    if lenient_issubclass(v, Enum):
        if issubclass(v, int):
            return 'int'
        elif issubclass(v, str):
            return 'str'
        else:
            return 'enum'

    try:
        return v.__name__
    except AttributeError:
        # happens with unions
        return str(v)


ExcType = Type[Exception]


@contextmanager
def change_exception(raise_exc: ExcType, *except_types: ExcType) -> Generator[None, None, None]:
    try:
        yield
    except except_types as e:
        raise raise_exc from e


def clean_docstring(d: str) -> str:
    return dedent(d).strip(' \r\n\t')


def list_like(v: AnyType) -> bool:
    return isinstance(v, (list, tuple, set)) or inspect.isgenerator(v)


def validate_field_name(bases: List[Type['BaseModel']], field_name: str) -> None:
    """
    Ensure that the field's name does not shadow an existing attribute of the model.
    """
    for base in bases:
        if getattr(base, field_name, None):
            raise NameError(
                f'Field name "{field_name}" shadows a BaseModel attribute; '
                f'use a different field name with "alias=\'{field_name}\'".'
            )


@lru_cache(maxsize=None)
def url_regex_generator(*, relative: bool, require_tld: bool) -> Pattern[str]:
    """
    Url regex generator taken from Marshmallow library,
    for details please follow library source code:
        https://github.com/marshmallow-code/marshmallow/blob/298870ef6c089fb4d91efae9ca4168453ffe00d2/marshmallow/validate.py#L37
    """
    return re.compile(
        r''.join(
            (
                r'^',
                r'(' if relative else r'',
                r'(?:[a-z0-9\.\-\+]*)://',  # scheme is validated separately
                r'(?:[^:@]+?:[^:@]*?@|)',  # basic auth
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+',
                r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|',  # domain...
                r'localhost|',  # localhost...
                (
                    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.?)|' if not require_tld else r''
                ),  # allow dotless hostnames
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|',  # ...or ipv4
                r'\[[A-F0-9]*:[A-F0-9:]+\])',  # ...or ipv6
                r'(?::\d+)?',  # optional port
                r')?' if relative else r'',  # host is optional, allow for relative URLs
                r'(?:/?|[/?]\S+)$',
            )
        ),
        re.IGNORECASE,
    )


def lenient_issubclass(cls: Any, class_or_tuple: Union[AnyType, Tuple[AnyType, ...]]) -> bool:
    return isinstance(cls, type) and issubclass(cls, class_or_tuple)


def in_ipython() -> bool:
    """
    Check whether we're in an ipython environment, including jupyter notebooks.
    """
    try:
        __IPYTHON__  # type: ignore
    except NameError:
        return False
    else:  # pragma: no cover
        return True


def resolve_annotations(raw_annotations: Dict[str, AnyType], module_name: Optional[str]) -> Dict[str, AnyType]:
    """
    Partially taken from typing.get_type_hints.

    Resolve string or ForwardRef annotations into type objects if possible.
    """
    if module_name:
        base_globals: Optional[Dict[str, Any]] = sys.modules[module_name].__dict__
    else:
        base_globals = None
    annotations = {}
    for name, value in raw_annotations.items():
        if isinstance(value, str):
            value = ForwardRef(value, is_argument=False)
        try:
            value = _eval_type(value, base_globals, None)
        except NameError:
            # this is ok, it can be fixed with update_forward_refs
            pass
        annotations[name] = value
    return annotations


def is_callable_type(type_: AnyType) -> bool:
    return type_ is Callable or getattr(type_, '__origin__', None) is Callable
