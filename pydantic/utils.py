import inspect
import re
from contextlib import contextmanager
from functools import lru_cache
from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Pattern, Set, Tuple, Type, Union, no_type_check

from . import errors
from .typing import AnyType

try:
    import email_validator
except ImportError:
    email_validator = None

if TYPE_CHECKING:  # pragma: no cover
    from .main import BaseModel  # noqa: F401
    from .typing import SetIntStr, DictIntStrAny, IntStr  # noqa: F401


PRETTY_REGEX = re.compile(r'([\w ]*?) *<(.*)> *')


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


def truncate(v: Union[str], *, max_len: int = 80) -> str:
    """
    Truncate a value and add a unicode ellipsis (three dots) to the end if it was too long
    """
    if isinstance(v, str) and len(v) > (max_len - 2):
        # -3 so quote + string + … + quote has correct length
        return (v[: (max_len - 3)] + '…').__repr__()
    try:
        v = v.__repr__()
    except TypeError:
        v = type(v).__repr__(v)  # in case v is a type
    if len(v) > max_len:
        v = v[: max_len - 1] + '…'
    return v


ExcType = Type[Exception]


@contextmanager
def change_exception(raise_exc: ExcType, *except_types: ExcType) -> Generator[None, None, None]:
    try:
        yield
    except except_types as e:
        raise raise_exc from e


def sequence_like(v: AnyType) -> bool:
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


def in_ipython() -> bool:
    """
    Check whether we're in an ipython environment, including jupyter notebooks.
    """
    try:
        eval('__IPYTHON__')
    except NameError:
        return False
    else:  # pragma: no cover
        return True


def almost_equal_floats(value_1: float, value_2: float, *, delta: float = 1e-8) -> bool:
    """
    Return True if two floats are almost equal
    """
    return abs(value_1 - value_2) <= delta


class GetterDict:
    """
    Hack to make object's smell just enough like dicts for validate_model.
    """

    __slots__ = ('_obj',)

    def __init__(self, obj: Any):
        self._obj = obj

    def get(self, item: Any, default: Any) -> Any:
        return getattr(self._obj, item, default)

    def keys(self) -> Set[Any]:
        """
        We don't want to get any other attributes of obj if the model didn't explicitly ask for them
        """
        return set()


class ValueItems:
    """
    Class for more convenient calculation of excluded or included fields on values.
    """

    __slots__ = ('_items', '_type')

    def __init__(self, value: Any, items: Union['SetIntStr', 'DictIntStrAny']) -> None:
        if TYPE_CHECKING:  # pragma: no cover
            self._items: Union['SetIntStr', 'DictIntStrAny']
            self._type: Type[Union[set, dict]]  # type: ignore

        # For further type checks speed-up
        if isinstance(items, dict):
            self._type = dict
        elif isinstance(items, set):
            self._type = set
        else:
            raise TypeError(f'Unexpected type of exclude value {type(items)}')

        if isinstance(value, (list, tuple)):
            items = self._normalize_indexes(items, len(value))

        self._items = items

    @no_type_check
    def is_excluded(self, item: Any) -> bool:
        """
        Check if item is fully excluded
        (value considered excluded if self._type is set and item contained in self._items
         or self._type is dict and self._items.get(item) is ...

        :param item: key or index of a value
        """
        if self._type is set:
            return item in self._items
        return self._items.get(item) is ...

    @no_type_check
    def is_included(self, item: Any) -> bool:
        """
        Check if value is contained in self._items

        :param item: key or index of value
        """
        return item in self._items

    @no_type_check
    def for_element(self, e: 'IntStr') -> Optional[Union['SetIntStr', 'DictIntStrAny']]:
        """
        :param e: key or index of element on value
        :return: raw values for elemet if self._items is dict and contain needed element
        """

        if self._type is dict:
            item = self._items.get(e)
            return item if item is not ... else None
        return None

    @no_type_check
    def _normalize_indexes(
        self, items: Union['SetIntStr', 'DictIntStrAny'], v_length: int
    ) -> Union['SetIntStr', 'DictIntStrAny']:
        """
        :param items: dict or set of indexes which will be normalized
        :param v_length: length of sequence indexes of which will be

        >>> self._normalize_indexes({0, -2, -1}, 4)
        {0, 2, 3}
        """
        if self._type is set:
            return {v_length + i if i < 0 else i for i in items}
        else:
            return {v_length + i if i < 0 else i: v for i, v in items.items()}

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self._type.__name__}({self._items})'
