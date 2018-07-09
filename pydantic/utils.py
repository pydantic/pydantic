import inspect
import re
from contextlib import contextmanager
from enum import Enum
from importlib import import_module
from textwrap import dedent
from typing import Tuple

from . import errors

try:
    import email_validator
except ImportError:
    email_validator = None

try:
    from typing import _TypingBase as typing_base
except ImportError:
    from typing import _Final as typing_base


PRETTY_REGEX = re.compile(r'([\w ]*?) *<(.*)> *')


def validate_email(value) -> Tuple[str, str]:
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
    if m:
        name, value = m.groups()
    else:
        name = None

    email = value.strip()

    try:
        email_validator.validate_email(email, check_deliverability=False)
    except email_validator.EmailNotValidError as e:
        raise errors.EmailError() from e

    return name or email[:email.index('@')], email.lower()


def _rfc_1738_quote(text):
    return re.sub(r'[:@/]', lambda m: '%{:X}'.format(ord(m.group(0))), text)


def make_dsn(*,
             driver: str,
             user: str=None,
             password: str=None,
             host: str=None,
             port: str=None,
             name: str=None,
             query: str=None):
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


def import_string(dotted_path):
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


def truncate(v, *, max_len=80):
    """
    Truncate a value and add a unicode ellipsis (three dots) to the end if it was too long
    """
    if isinstance(v, str) and len(v) > (max_len - 2):
        # -3 so quote + string + … + quote has correct length
        return repr(v[:(max_len - 3)] + '…')
    v = repr(v)
    if len(v) > max_len:
        v = v[:max_len - 1] + '…'
    return v


def display_as_type(v):
    if not isinstance(v, typing_base) and not isinstance(v, type):
        v = type(v)

    if isinstance(v, type) and issubclass(v, Enum):
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


@contextmanager
def change_exception(raise_exc, *except_types):
    try:
        yield
    except except_types as e:
        raise raise_exc from e


def clean_docstring(d):
    return dedent(d).strip(' \r\n\t')


def list_like(v):
    return isinstance(v, (list, tuple, set)) or inspect.isgenerator(v)
