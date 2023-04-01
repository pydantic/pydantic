"""
Logic for interacting with type annotations, mostly extensions, shims and hacks to wrap python's typing module.
"""
from __future__ import annotations as _annotations

import sys
import types
import typing
from collections.abc import Callable
from types import GetSetDescriptorType
from typing import Any, ForwardRef

from typing_extensions import Annotated, Final, Literal, get_args, get_origin

__all__ = (
    'NoneType',
    'is_none_type',
    'is_callable_type',
    'is_literal_type',
    'all_literal_values',
    'is_annotated',
    'is_namedtuple',
    'is_new_type',
    'is_classvar',
    'is_finalvar',
    'WithArgsTypes',
    'typing_base',
    'origin_is_union',
    'NotRequired',
    'Required',
    'parent_frame_namespace',
    'get_type_hints',
    'EllipsisType',
    'add_module_globals',
    'get_cls_type_hints_lenient',
)

try:
    from typing import _TypingBase  # type: ignore[attr-defined]
except ImportError:
    from typing import _Final as _TypingBase  # type: ignore[attr-defined]

typing_base = _TypingBase


if sys.version_info < (3, 9):
    # python < 3.9 does not have GenericAlias (list[int], tuple[str, ...] and so on)
    TypingGenericAlias = ()
else:
    from typing import GenericAlias as TypingGenericAlias  # type: ignore


if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required
else:
    from typing import NotRequired, Required


if sys.version_info < (3, 10):

    def origin_is_union(tp: type[Any] | None) -> bool:
        return tp is typing.Union

    WithArgsTypes = (TypingGenericAlias,)

else:

    def origin_is_union(tp: type[Any] | None) -> bool:
        return tp is typing.Union or tp is types.UnionType  # noqa: E721

    WithArgsTypes = typing._GenericAlias, types.GenericAlias, types.UnionType  # type: ignore[attr-defined]


if sys.version_info < (3, 10):
    NoneType = type(None)
    EllipsisType = type(Ellipsis)
else:
    from types import EllipsisType as EllipsisType
    from types import NoneType as NoneType


NONE_TYPES: tuple[Any, Any, Any] = (None, NoneType, Literal[None])


TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type


if sys.version_info < (3, 8):
    # Even though this implementation is slower, we need it for python 3.7:
    # In python 3.7 "Literal" is not a builtin type and uses a different
    # mechanism.
    # for this reason `Literal[None] is Literal[None]` evaluates to `False`,
    # breaking the faster implementation used for the other python versions.

    def is_none_type(type_: Any) -> bool:
        return type_ in NONE_TYPES

elif sys.version_info[:2] == (3, 8):

    def is_none_type(type_: Any) -> bool:
        for none_type in NONE_TYPES:
            if type_ is none_type:
                return True
        # With python 3.8, specifically 3.8.10, Literal "is" checks are very flakey
        # can change on very subtle changes like use of types in other modules,
        # hopefully this check avoids that issue.
        if is_literal_type(type_):  # pragma: no cover
            return all_literal_values(type_) == [None]
        return False

else:

    def is_none_type(type_: Any) -> bool:
        for none_type in NONE_TYPES:
            if type_ is none_type:
                return True
        return False


def is_callable_type(type_: type[Any]) -> bool:
    return type_ is Callable or get_origin(type_) is Callable


def is_literal_type(type_: type[Any]) -> bool:
    return Literal is not None and get_origin(type_) is Literal


def literal_values(type_: type[Any]) -> tuple[Any, ...]:
    return get_args(type_)


def all_literal_values(type_: type[Any]) -> list[Any]:
    """
    This method is used to retrieve all Literal values as
    Literal can be used recursively (see https://www.python.org/dev/peps/pep-0586)
    e.g. `Literal[Literal[Literal[1, 2, 3], "foo"], 5, None]`
    """
    if not is_literal_type(type_):
        return [type_]

    values = literal_values(type_)
    return list(x for value in values for x in all_literal_values(value))


def is_annotated(ann_type: Any) -> bool:
    from ._utils import lenient_issubclass

    origin = get_origin(ann_type)
    return origin is not None and lenient_issubclass(origin, Annotated)


def is_namedtuple(type_: type[Any]) -> bool:
    """
    Check if a given class is a named tuple.
    It can be either a `typing.NamedTuple` or `collections.namedtuple`
    """
    from ._utils import lenient_issubclass

    return lenient_issubclass(type_, tuple) and hasattr(type_, '_fields')


test_new_type = typing.NewType('test_new_type', str)


def is_new_type(type_: type[Any]) -> bool:
    """
    Check whether type_ was created using typing.NewType.

    Can't use isinstance because it fails <3.10.
    """
    return isinstance(type_, test_new_type.__class__) and hasattr(type_, '__supertype__')  # type: ignore[arg-type]


def _check_classvar(v: type[Any] | None) -> bool:
    if v is None:
        return False

    return v.__class__ == typing.ClassVar.__class__ and getattr(v, '_name', None) == 'ClassVar'


def is_classvar(ann_type: type[Any]) -> bool:
    if _check_classvar(ann_type) or _check_classvar(get_origin(ann_type)):
        return True

    # this is an ugly workaround for class vars that contain forward references and are therefore themselves
    # forward references, see #3679
    if ann_type.__class__ == typing.ForwardRef and ann_type.__forward_arg__.startswith('ClassVar['):
        return True

    return False


def _check_finalvar(v: type[Any] | None) -> bool:
    """
    Check if a given type is a `typing.Final` type.
    """
    if v is None:
        return False

    return v.__class__ == Final.__class__ and (sys.version_info < (3, 8) or getattr(v, '_name', None) == 'Final')


def is_finalvar(ann_type: type[Any]) -> bool:
    return _check_finalvar(ann_type) or _check_finalvar(get_origin(ann_type))


def parent_frame_namespace(*, parent_depth: int = 2) -> dict[str, Any] | None:
    """
    We allow use of items in parent namespace to get around the issue with `get_type_hints` only looking in the
    global module namespace. See https://github.com/pydantic/pydantic/issues/2678#issuecomment-1008139014 -> Scope
    and suggestion at the end of the next comment by @gvanrossum.

    WARNING 1: it matters exactly where this is called. By default, this function will build a namespace from the
    parent of where it is called.

    WARNING 2: this only looks in the parent namespace, not other parents since (AFAIK) there's no way to collect a
    dict of exactly what's in scope. Using `f_back` would work sometimes but would be very wrong and confusing in many
    other cases. See https://discuss.python.org/t/is-there-a-way-to-access-parent-nested-namespaces/20659.
    """
    frame = sys._getframe(parent_depth)
    # if f_back is None, it's the global module namespace and we don't need to include it here
    if frame.f_back is None:
        return None
    else:
        return frame.f_locals


def add_module_globals(obj: Any, globalns: dict[str, Any] | None) -> dict[str, Any]:
    module_name = getattr(obj, '__module__', None)
    if module_name:
        try:
            module_globalns = sys.modules[module_name].__dict__
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            pass
        else:
            if globalns:
                return {**module_globalns, **globalns}
            else:
                # copy module globals to make sure it can't be updated later
                return module_globalns.copy()

    return globalns or {}


def get_cls_type_hints_lenient(obj: Any, globalns: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Collect annotations from a class, including those from parent classes.

    Unlike `typing.get_type_hints`, this function will not evaluate forward references so won't error if
    a forward reference is not resolvable.
    """
    # TODO: Try handling typevars_map here
    hints = {}
    for base in reversed(obj.__mro__):
        ann = base.__dict__.get('__annotations__')
        localns = dict(vars(base))
        if ann is not None and ann is not GetSetDescriptorType:
            for name, value in ann.items():
                if value is None:
                    value = NoneType
                elif isinstance(value, str):
                    value = ForwardRef(value, is_argument=False, is_class=True)

                try:
                    hints[name] = typing._eval_type(value, globalns, localns)  # type: ignore[attr-defined]
                except NameError:
                    # the point of this function is to be tolerant to this case
                    hints[name] = value
    return hints


if sys.version_info < (3, 9):

    def ForwardRefWrapper(arg: Any, is_argument: bool = True, *, is_class: bool = False) -> typing.ForwardRef:
        """
        Wrapper for ForwardRef that accounts for the `is_class` argument missing in older versions.
        The `module` argument is omitted as it breaks <3.9 and isn't used in the calls below.

        See https://github.com/python/cpython/pull/28560 for some background

        Implemented as EAFP with memory.
        """
        global fr_has_is_class

        if not fr_has_is_class:
            return typing.ForwardRef(arg, is_argument)

        try:
            return typing.ForwardRef(arg, is_argument, is_class=is_class)
        except TypeError:
            fr_has_is_class = False
            return typing.ForwardRef(arg, is_argument)

    ForwardRef = ForwardRefWrapper  # noqa F811

if sys.version_info >= (3, 10):
    get_type_hints = typing.get_type_hints

else:
    """
    For older versions of python, we have a custom implementation of `get_type_hints` which is a close as possible to
    the implementation in CPython 3.10.8.
    """
    fr_has_is_class = True

    @typing.no_type_check
    def get_type_hints(  # noqa: C901
        obj: Any,
        globalns: dict[str, Any] | None = None,
        localns: dict[str, Any] | None = None,
        include_extras: bool = False,
    ) -> dict[str, Any]:  # pragma: no cover
        """
        Taken verbatim from python 3.10.8 unchanged, except:
        * type annotations of the function definition above.
        * prefixing `typing.` where appropriate
        * Use `ForwardRefWrapper` instead of `typing.ForwardRef`

        https://github.com/python/cpython/blob/aaaf5174241496afca7ce4d4584570190ff972fe/Lib/typing.py#L1773-L1875

        DO NOT CHANGE THIS METHOD UNLESS ABSOLUTELY NECESSARY.
        ======================================================

        Return type hints for an object.

        This is often the same as obj.__annotations__, but it handles
        forward references encoded as string literals, adds Optional[t] if a
        default value equal to None is set and recursively replaces all
        'Annotated[T, ...]' with 'T' (unless 'include_extras=True').

        The argument may be a module, class, method, or function. The annotations
        are returned as a dictionary. For classes, annotations include also
        inherited members.

        TypeError is raised if the argument is not of a type that can contain
        annotations, and an empty dictionary is returned if no annotations are
        present.

        BEWARE -- the behavior of globalns and localns is counterintuitive
        (unless you are familiar with how eval() and exec() work).  The
        search order is locals first, then globals.

        - If no dict arguments are passed, an attempt is made to use the
          globals from obj (or the respective module's globals for classes),
          and these are also used as the locals.  If the object does not appear
          to have globals, an empty dictionary is used.  For classes, the search
          order is globals first then locals.

        - If one dict argument is passed, it is used for both globals and
          locals.

        - If two dict arguments are passed, they specify globals and
          locals, respectively.
        """

        if getattr(obj, '__no_type_check__', None):
            return {}
        # Classes require a special treatment.
        if isinstance(obj, type):
            hints = {}
            for base in reversed(obj.__mro__):
                if globalns is None:
                    base_globals = getattr(sys.modules.get(base.__module__, None), '__dict__', {})
                else:
                    base_globals = globalns
                ann = base.__dict__.get('__annotations__', {})
                if isinstance(ann, types.GetSetDescriptorType):
                    ann = {}
                base_locals = dict(vars(base)) if localns is None else localns
                if localns is None and globalns is None:
                    # This is surprising, but required.  Before Python 3.10,
                    # get_type_hints only evaluated the globalns of
                    # a class.  To maintain backwards compatibility, we reverse
                    # the globalns and localns order so that eval() looks into
                    # *base_globals* first rather than *base_locals*.
                    # This only affects ForwardRefs.
                    base_globals, base_locals = base_locals, base_globals
                for name, value in ann.items():
                    if value is None:
                        value = type(None)
                    if isinstance(value, str):
                        value = ForwardRef(value, is_argument=False, is_class=True)

                    value = typing._eval_type(value, base_globals, base_locals)
                    hints[name] = value
            return hints if include_extras else {k: typing._strip_annotations(t) for k, t in hints.items()}

        if globalns is None:
            if isinstance(obj, types.ModuleType):
                globalns = obj.__dict__
            else:
                nsobj = obj
                # Find globalns for the unwrapped object.
                while hasattr(nsobj, '__wrapped__'):
                    nsobj = nsobj.__wrapped__
                globalns = getattr(nsobj, '__globals__', {})
            if localns is None:
                localns = globalns
        elif localns is None:
            localns = globalns
        hints = getattr(obj, '__annotations__', None)
        if hints is None:
            # Return empty annotations for something that _could_ have them.
            if isinstance(obj, typing._allowed_types):
                return {}
            else:
                raise TypeError('{!r} is not a module, class, method, ' 'or function.'.format(obj))
        defaults = typing._get_defaults(obj)
        hints = dict(hints)
        for name, value in hints.items():
            if value is None:
                value = type(None)
            if isinstance(value, str):
                # class-level forward refs were handled above, this must be either
                # a module-level annotation or a function argument annotation

                value = ForwardRef(
                    value,
                    is_argument=not isinstance(obj, types.ModuleType),
                    is_class=False,
                )
            value = typing._eval_type(value, globalns, localns)
            if name in defaults and defaults[name] is None:
                value = typing.Optional[value]
            hints[name] = value
        return hints if include_extras else {k: typing._strip_annotations(t) for k, t in hints.items()}


if sys.version_info < (3, 9):

    def evaluate_fwd_ref(
        ref: ForwardRef, globalns: dict[str, Any] | None = None, localns: dict[str, Any] | None = None
    ) -> Any:
        return ref._evaluate(globalns=globalns, localns=localns)

else:

    def evaluate_fwd_ref(
        ref: ForwardRef, globalns: dict[str, Any] | None = None, localns: dict[str, Any] | None = None
    ) -> Any:
        return ref._evaluate(globalns=globalns, localns=localns, recursive_guard=frozenset())
