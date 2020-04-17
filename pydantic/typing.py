import sys
from enum import Enum
from typing import (  # type: ignore
    TYPE_CHECKING,
    AbstractSet,
    Any,
    ClassVar,
    Dict,
    Generator,
    List,
    Mapping,
    NewType,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    _eval_type,
)

try:
    from typing import _TypingBase as typing_base  # type: ignore
except ImportError:
    from typing import _Final as typing_base  # type: ignore

try:
    from typing import ForwardRef  # type: ignore

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Type[Any]:
        return type_._evaluate(globalns, localns)


except ImportError:
    # python 3.6
    from typing import _ForwardRef as ForwardRef  # type: ignore

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Type[Any]:
        return type_._eval_type(globalns, localns)


if sys.version_info < (3, 7):
    from typing import Callable as Callable

    AnyCallable = Callable[..., Any]
    NoArgAnyCallable = Callable[[], Any]
else:
    from collections.abc import Callable as Callable
    from typing import Callable as TypingCallable

    AnyCallable = TypingCallable[..., Any]
    NoArgAnyCallable = TypingCallable[[], Any]

if sys.version_info < (3, 8):
    if TYPE_CHECKING:
        from typing_extensions import Literal
    else:  # due to different mypy warnings raised during CI for python 3.7 and 3.8
        try:
            from typing_extensions import Literal
        except ImportError:
            Literal = None
else:
    from typing import Literal

if TYPE_CHECKING:
    from .fields import ModelField

    TupleGenerator = Generator[Tuple[str, Any], None, None]
    DictStrAny = Dict[str, Any]
    DictAny = Dict[Any, Any]
    SetStr = Set[str]
    ListStr = List[str]
    IntStr = Union[int, str]
    AbstractSetIntStr = AbstractSet[IntStr]
    DictIntStrAny = Dict[IntStr, Any]
    MappingIntStrAny = Mapping[IntStr, Any]
    CallableGenerator = Generator[AnyCallable, None, None]
    ReprArgs = Sequence[Tuple[Optional[str], Any]]

__all__ = (
    'ForwardRef',
    'Callable',
    'AnyCallable',
    'NoArgAnyCallable',
    'AnyType',
    'NoneType',
    'display_as_type',
    'resolve_annotations',
    'is_callable_type',
    'is_literal_type',
    'literal_values',
    'Literal',
    'is_new_type',
    'new_type_supertype',
    'is_classvar',
    'update_field_forward_refs',
    'TupleGenerator',
    'DictStrAny',
    'DictAny',
    'SetStr',
    'ListStr',
    'IntStr',
    'AbstractSetIntStr',
    'DictIntStrAny',
    'CallableGenerator',
    'ReprArgs',
    'CallableGenerator',
)


AnyType = Type[Any]
NoneType = None.__class__


def display_as_type(v: AnyType) -> str:
    if not isinstance(v, typing_base) and not isinstance(v, type):
        v = v.__class__

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
        # happens with typing objects
        return str(v).replace('typing.', '')


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
            if sys.version_info >= (3, 7):
                value = ForwardRef(value, is_argument=False)
            else:
                value = ForwardRef(value)
        try:
            value = _eval_type(value, base_globals, None)
        except NameError:
            # this is ok, it can be fixed with update_forward_refs
            pass
        annotations[name] = value
    return annotations


def is_callable_type(type_: AnyType) -> bool:
    return type_ is Callable or getattr(type_, '__origin__', None) is Callable


if sys.version_info >= (3, 7):

    def is_literal_type(type_: AnyType) -> bool:
        return Literal is not None and getattr(type_, '__origin__', None) is Literal

    def literal_values(type_: AnyType) -> Tuple[Any, ...]:
        return type_.__args__


else:

    def is_literal_type(type_: AnyType) -> bool:
        return Literal is not None and hasattr(type_, '__values__') and type_ == Literal[type_.__values__]

    def literal_values(type_: AnyType) -> Tuple[Any, ...]:
        return type_.__values__


test_type = NewType('test_type', str)


def is_new_type(type_: AnyType) -> bool:
    """
    Check whether type_ was created using typing.NewType
    """
    return isinstance(type_, test_type.__class__) and hasattr(type_, '__supertype__')  # type: ignore


def new_type_supertype(type_: AnyType) -> AnyType:
    while hasattr(type_, '__supertype__'):
        type_ = type_.__supertype__
    return type_


def _check_classvar(v: AnyType) -> bool:
    return v.__class__ == ClassVar.__class__ and (sys.version_info < (3, 7) or getattr(v, '_name', None) == 'ClassVar')


def is_classvar(ann_type: AnyType) -> bool:
    return _check_classvar(ann_type) or _check_classvar(getattr(ann_type, '__origin__', None))


def update_field_forward_refs(field: 'ModelField', globalns: Any, localns: Any) -> None:
    """
    Try to update ForwardRefs on fields based on this ModelField, globalns and localns.
    """
    if field.type_.__class__ == ForwardRef:
        field.type_ = evaluate_forwardref(field.type_, globalns, localns or None)
        field.prepare()
    if field.sub_fields:
        for sub_f in field.sub_fields:
            update_field_forward_refs(sub_f, globalns=globalns, localns=localns)


def get_class(type_: AnyType) -> Union[None, bool, AnyType]:
    """
    Tries to get the class of a Type[T] annotation. Returns True if Type is used
    without brackets. Otherwise returns None.
    """
    try:
        origin = getattr(type_, '__origin__')
        if origin is None:  # Python 3.6
            origin = type_
        if issubclass(origin, Type):  # type: ignore
            if type_.__args__ is None or not isinstance(type_.__args__[0], type):
                return True
            return type_.__args__[0]
    except AttributeError:
        pass
    return None
