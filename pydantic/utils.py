import warnings
from itertools import islice
from types import GeneratorType
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    no_type_check,
)

from .typing import AnyType, display_as_type
from .version import version_info

if TYPE_CHECKING:
    from inspect import Signature
    from .main import BaseModel, BaseConfig  # noqa: F401
    from .typing import AbstractSetIntStr, DictIntStrAny, IntStr, MappingIntStrAny, ReprArgs  # noqa: F401
    from .fields import ModelField  # noqa: F401
    from .dataclasses import DataclassType  # noqa: F401

__all__ = (
    'import_string',
    'sequence_like',
    'validate_field_name',
    'lenient_issubclass',
    'in_ipython',
    'deep_update',
    'update_not_none',
    'almost_equal_floats',
    'get_model',
    'to_camel',
    'PyObjectStr',
    'Representation',
    'GetterDict',
    'ValueItems',
    'version_info',  # required here to match behaviour in v1.3
)


def import_string(dotted_path: str) -> Any:
    """
    Stolen approximately from django. Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails.
    """
    from importlib import import_module

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
    warnings.warn('`truncate` is no-longer used by pydantic and is deprecated', DeprecationWarning)
    if isinstance(v, str) and len(v) > (max_len - 2):
        # -3 so quote + string + … + quote has correct length
        return (v[: (max_len - 3)] + '…').__repr__()
    try:
        v = v.__repr__()
    except TypeError:
        v = v.__class__.__repr__(v)  # in case v is a type
    if len(v) > max_len:
        v = v[: max_len - 1] + '…'
    return v


def sequence_like(v: AnyType) -> bool:
    return isinstance(v, (list, tuple, set, frozenset, GeneratorType))


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


KeyType = TypeVar('KeyType')


def deep_update(mapping: Dict[KeyType, Any], updating_mapping: Dict[KeyType, Any]) -> Dict[KeyType, Any]:
    updated_mapping = mapping.copy()
    for k, v in updating_mapping.items():
        if k in mapping and isinstance(mapping[k], dict) and isinstance(v, dict):
            updated_mapping[k] = deep_update(mapping[k], v)
        else:
            updated_mapping[k] = v
    return updated_mapping


def update_not_none(mapping: Dict[Any, Any], **update: Any) -> None:
    mapping.update({k: v for k, v in update.items() if v is not None})


def almost_equal_floats(value_1: float, value_2: float, *, delta: float = 1e-8) -> bool:
    """
    Return True if two floats are almost equal
    """
    return abs(value_1 - value_2) <= delta


def generate_model_signature(
    init: Callable[..., None], fields: Dict[str, 'ModelField'], config: Type['BaseConfig']
) -> 'Signature':
    """
    Generate signature for model based on its fields
    """
    from inspect import Parameter, Signature, signature

    present_params = signature(init).parameters.values()
    merged_params: Dict[str, Parameter] = {}
    var_kw = None
    use_var_kw = False

    for param in islice(present_params, 1, None):  # skip self arg
        if param.kind is param.VAR_KEYWORD:
            var_kw = param
            continue
        merged_params[param.name] = param

    if var_kw:  # if custom init has no var_kw, fields which are not declared in it cannot be passed through
        allow_names = config.allow_population_by_field_name
        for field_name, field in fields.items():
            param_name = field.alias
            if field_name in merged_params or param_name in merged_params:
                continue
            elif not param_name.isidentifier():
                if allow_names and field_name.isidentifier():
                    param_name = field_name
                else:
                    use_var_kw = True
                    continue

            # TODO: replace annotation with actual expected types once #1055 solved
            kwargs = {'default': field.default} if not field.required else {}
            merged_params[param_name] = Parameter(
                param_name, Parameter.KEYWORD_ONLY, annotation=field.outer_type_, **kwargs
            )

    if config.extra is config.extra.allow:
        use_var_kw = True

    if var_kw and use_var_kw:
        # Make sure the parameter for extra kwargs
        # does not have the same name as a field
        default_model_signature = [
            ('__pydantic_self__', Parameter.POSITIONAL_OR_KEYWORD),
            ('data', Parameter.VAR_KEYWORD),
        ]
        if [(p.name, p.kind) for p in present_params] == default_model_signature:
            # if this is the standard model signature, use extra_data as the extra args name
            var_kw_name = 'extra_data'
        else:
            # else start from var_kw
            var_kw_name = var_kw.name

        # generate a name that's definitely unique
        while var_kw_name in fields:
            var_kw_name += '_'
        merged_params[var_kw_name] = var_kw.replace(name=var_kw_name)

    return Signature(parameters=list(merged_params.values()), return_annotation=None)


def get_model(obj: Union[Type['BaseModel'], Type['DataclassType']]) -> Type['BaseModel']:
    from .main import BaseModel  # noqa: F811

    try:
        model_cls = obj.__pydantic_model__  # type: ignore
    except AttributeError:
        model_cls = obj

    if not issubclass(model_cls, BaseModel):
        raise TypeError('Unsupported type, must be either BaseModel or dataclass')
    return model_cls


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class PyObjectStr(str):
    """
    String class where repr doesn't include quotes. Useful with Representation when you want to return a string
    representation of something that valid (or pseudo-valid) python.
    """

    def __repr__(self) -> str:
        return str(self)


class Representation:
    """
    Mixin to provide __str__, __repr__, and __pretty__ methods. See #884 for more details.

    __pretty__ is used by [devtools](https://python-devtools.helpmanual.io/) to provide human readable representations
    of objects.
    """

    __slots__: Tuple[str, ...] = tuple()

    def __repr_args__(self) -> 'ReprArgs':
        """
        Returns the attributes to show in __str__, __repr__, and __pretty__ this is generally overridden.

        Can either return:
        * name - value pairs, e.g.: `[('foo_name', 'foo'), ('bar_name', ['b', 'a', 'r'])]`
        * or, just values, e.g.: `[(None, 'foo'), (None, ['b', 'a', 'r'])]`
        """
        attrs = ((s, getattr(self, s)) for s in self.__slots__)
        return [(a, v) for a, v in attrs if v is not None]

    def __repr_name__(self) -> str:
        """
        Name of the instance's class, used in __repr__.
        """
        return self.__class__.__name__

    def __repr_str__(self, join_str: str) -> str:
        return join_str.join(repr(v) if a is None else f'{a}={v!r}' for a, v in self.__repr_args__())

    def __pretty__(self, fmt: Callable[[Any], Any], **kwargs: Any) -> Generator[Any, None, None]:
        """
        Used by devtools (https://python-devtools.helpmanual.io/) to provide a human readable representations of objects
        """
        yield self.__repr_name__() + '('
        yield 1
        for name, value in self.__repr_args__():
            if name is not None:
                yield name + '='
            yield fmt(value)
            yield ','
            yield 0
        yield -1
        yield ')'

    def __str__(self) -> str:
        return self.__repr_str__(' ')

    def __repr__(self) -> str:
        return f'{self.__repr_name__()}({self.__repr_str__(", ")})'


class GetterDict(Representation):
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

    def keys(self) -> List[Any]:
        """
        Keys of the pseudo dictionary, uses a list not set so order information can be maintained like python
        dictionaries.
        """
        return list(self)

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

    def __repr_args__(self) -> 'ReprArgs':
        return [(None, dict(self))]  # type: ignore

    def __repr_name__(self) -> str:
        return f'GetterDict[{display_as_type(self._obj)}]'


class ValueItems(Representation):
    """
    Class for more convenient calculation of excluded or included fields on values.
    """

    __slots__ = ('_items', '_type')

    def __init__(self, value: Any, items: Union['AbstractSetIntStr', 'MappingIntStrAny']) -> None:
        if TYPE_CHECKING:
            self._items: Union['AbstractSetIntStr', 'MappingIntStrAny']
            self._type: Type[Union[set, dict]]  # type: ignore

        # For further type checks speed-up
        if isinstance(items, dict):
            self._type = dict
        elif isinstance(items, AbstractSet):
            self._type = set
        else:
            raise TypeError(f'Unexpected type of exclude value {items.__class__}')

        if isinstance(value, (list, tuple)):
            try:
                items = self._normalize_indexes(items, len(value))
            except TypeError as e:
                raise TypeError(
                    'Excluding fields from a sequence of sub-models or dicts must be performed index-wise: '
                    'expected integer keys or keyword "__all__"'
                ) from e

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
    def for_element(self, e: 'IntStr') -> Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']]:
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
        self, items: Union['AbstractSetIntStr', 'MappingIntStrAny'], v_length: int
    ) -> Union['AbstractSetIntStr', 'DictIntStrAny']:
        """
        :param items: dict or set of indexes which will be normalized
        :param v_length: length of sequence indexes of which will be

        >>> self._normalize_indexes({0, -2, -1}, 4)
        {0, 2, 3}
        >>> self._normalize_indexes({'__all__'}, 4)
        {0, 1, 2, 3}
        """
        if self._type is set:
            if '__all__' in items:
                if items != {'__all__'}:
                    raise ValueError('set with keyword "__all__" must not contain other elements')
                return {i for i in range(v_length)}
            return {v_length + i if i < 0 else i for i in items}
        else:
            normalized_items = {v_length + i if i < 0 else i: v for i, v in items.items() if i != '__all__'}
            all_set = items.get('__all__')
            if all_set:
                for i in range(v_length):
                    normalized_items.setdefault(i, set()).update(all_set)

            return normalized_items

    def __repr_args__(self) -> 'ReprArgs':
        return [(None, self._items)]
