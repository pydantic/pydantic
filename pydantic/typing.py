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
    cast,
)

try:
    from typing import _TypingBase as typing_base  # type: ignore
except ImportError:
    from typing import _Final as typing_base  # type: ignore


if sys.version_info < (3, 7):
    if TYPE_CHECKING:

        class ForwardRef:
            def __init__(self, arg: Any):
                pass

            def _eval_type(self, globalns: Any, localns: Any) -> Any:
                pass

    else:
        from typing import _ForwardRef as ForwardRef
else:
    from typing import ForwardRef


if sys.version_info < (3, 7):

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        return type_._eval_type(globalns, localns)


elif sys.version_info < (3, 9):

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        return type_._evaluate(globalns, localns)


else:

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        # Even though it is the right signature for python 3.9, mypy complains with
        # `error: Too many arguments for "_evaluate" of "ForwardRef"` hence the cast...
        return cast(Any, type_)._evaluate(globalns, localns, set())


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

    def get_args(t: Type[Any]) -> Tuple[Any, ...]:
        return getattr(t, '__args__', ())

    def get_origin(t: Type[Any]) -> Optional[Type[Any]]:
        return getattr(t, '__origin__', None)


else:
    from typing import Literal, get_args as typing_get_args, get_origin as typing_get_origin

    def get_origin(tp: Type[Any]) -> Type[Any]:
        """
        We can't directly use `typing.get_origin` since we need a fallback to support
        custom generic classes like `ConstrainedList`
        It should be useless once https://github.com/cython/cython/issues/3537 is
        solved and https://github.com/samuelcolvin/pydantic/pull/1753 is merged.
        """
        return typing_get_origin(tp) or getattr(tp, '__origin__', None)

    def generic_get_args(tp: Type[Any]) -> Tuple[Any, ...]:
        """
        In python 3.9, `typing.Dict`, `typing.List`, ...
        do have an empty `__args__` by default (instead of the generic ~T for example).
        In order to still support `Dict` for example and consider it as `Dict[Any, Any]`,
        we retrieve the `_nparams` value that tells us how many parameters it needs.
        """
        if hasattr(tp, '_nparams'):
            return (Any,) * tp._nparams
        return ()

    def get_args(tp: Type[Any]) -> Tuple[Any, ...]:
        """Get type arguments with all substitutions performed.

        For unions, basic simplifications used by Union constructor are performed.
        Examples::
            get_args(Dict[str, int]) == (str, int)
            get_args(int) == ()
            get_args(Union[int, Union[T, int], str][int]) == (int, str)
            get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
            get_args(Callable[[], T][int]) == ([], int)
        """
        try:
            args = typing_get_args(tp)
        except IndexError:
            args = ()
        # the fallback is needed for the same reasons as `get_origin` (see above)
        return args or getattr(tp, '__args__', ()) or generic_get_args(tp)


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
    'get_args',
    'get_origin',
)


NoneType = None.__class__


def display_as_type(v: Type[Any]) -> str:
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


def resolve_annotations(raw_annotations: Dict[str, Type[Any]], module_name: Optional[str]) -> Dict[str, Type[Any]]:
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


def is_callable_type(type_: Type[Any]) -> bool:
    return type_ is Callable or get_origin(type_) is Callable


if sys.version_info >= (3, 7):

    def is_literal_type(type_: Type[Any]) -> bool:
        return Literal is not None and get_origin(type_) is Literal

    def literal_values(type_: Type[Any]) -> Tuple[Any, ...]:
        return get_args(type_)


else:

    def is_literal_type(type_: Type[Any]) -> bool:
        return Literal is not None and hasattr(type_, '__values__') and type_ == Literal[type_.__values__]

    def literal_values(type_: Type[Any]) -> Tuple[Any, ...]:
        return type_.__values__


def all_literal_values(type_: Type[Any]) -> Tuple[Any, ...]:
    """
    This method is used to retrieve all Literal values as
    Literal can be used recursively (see https://www.python.org/dev/peps/pep-0586)
    e.g. `Literal[Literal[Literal[1, 2, 3], "foo"], 5, None]`
    """
    if not is_literal_type(type_):
        return (type_,)

    values = literal_values(type_)
    return tuple(x for value in values for x in all_literal_values(value))


test_type = NewType('test_type', str)


def is_new_type(type_: Type[Any]) -> bool:
    """
    Check whether type_ was created using typing.NewType
    """
    return isinstance(type_, test_type.__class__) and hasattr(type_, '__supertype__')  # type: ignore


def new_type_supertype(type_: Type[Any]) -> Type[Any]:
    while hasattr(type_, '__supertype__'):
        type_ = type_.__supertype__
    return type_


def _check_classvar(v: Optional[Type[Any]]) -> bool:
    if v is None:
        return False

    return v.__class__ == ClassVar.__class__ and (sys.version_info < (3, 7) or getattr(v, '_name', None) == 'ClassVar')


def is_classvar(ann_type: Type[Any]) -> bool:
    return _check_classvar(ann_type) or _check_classvar(get_origin(ann_type))


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


def get_class(type_: Type[Any]) -> Union[None, bool, Type[Any]]:
    """
    Tries to get the class of a Type[T] annotation. Returns True if Type is used
    without brackets. Otherwise returns None.
    """
    try:
        origin = get_origin(type_)
        if origin is None:  # Python 3.6
            origin = type_
        if issubclass(origin, Type):  # type: ignore
            if not get_args(type_) or not isinstance(get_args(type_)[0], type):
                return True
            return get_args(type_)[0]
    except (AttributeError, TypeError):
        pass
    return None
