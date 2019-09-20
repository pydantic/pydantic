import inspect
from importlib import import_module
from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Set, Tuple, Type, Union, no_type_check

from .typing import AnyType, display_as_type

try:
    from typing_extensions import Literal
except ImportError:
    Literal = None  # type: ignore


if TYPE_CHECKING:  # pragma: no cover
    from .main import BaseModel  # noqa: F401
    from .typing import SetIntStr, DictIntStrAny, DictStrAny, IntStr  # noqa: F401


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


def sequence_like(v: AnyType) -> bool:
    return isinstance(v, (list, tuple, set, frozenset)) or inspect.isgenerator(v)


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


def lenient_issubclass(cls: Any, class_or_tuple: Union[AnyType, Tuple[AnyType, ...]]) -> bool:
    return isinstance(cls, type) and issubclass(cls, class_or_tuple)


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

    We can't inherit from Mapping[str, Any] because it upsets cython so we have to implement all methods ourselves.
    """

    __slots__ = ('_obj',)

    def __init__(self, obj: Any):
        self._obj = obj

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self._obj, key)
        except AttributeError as e:
            raise KeyError(key) from e

    def get(self, key: Any, default: Any = None) -> Any:
        return getattr(self._obj, key, default)

    def extra_keys(self) -> Set[Any]:
        """
        We don't want to get any other attributes of obj if the model didn't explicitly ask for them
        """
        return set()

    def keys(self) -> Set[Any]:
        return set(list(self))

    def as_dict(self) -> 'DictStrAny':
        """
        This is required to maintain order since ``dict(self)`` uses ``self.keys()`` which does not maintain order.
        """
        return dict(self.items())

    def values(self) -> List[Any]:
        return [self[k] for k in self]

    def items(self) -> Iterator[Tuple[str, Any]]:
        for k in self:
            yield k, self.get(k)

    def __iter__(self) -> Iterator[str]:
        for name in dir(self._obj):
            if not name.startswith('_'):
                yield name

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __contains__(self, item: Any) -> bool:
        return item in self.keys()

    def __eq__(self, other: Any) -> bool:
        return dict(self) == dict(other.items())  # type: ignore

    def __repr__(self) -> str:
        return f'<GetterDict({display_as_type(self._obj)}) {self.as_dict()}>'


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
