from __future__ import annotations

import operator
import sys
import types
import typing
from collections import ChainMap
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from functools import reduce
from itertools import zip_longest
from types import prepare_class
from typing import TYPE_CHECKING, Annotated, Any, TypedDict, TypeVar, cast
from weakref import WeakValueDictionary

import typing_extensions
from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin

from . import _typing_extra
from ._core_utils import get_type_ref
from ._forward_ref import PydanticRecursiveRef
from ._utils import all_identical, is_model_class

if TYPE_CHECKING:
    from ..main import BaseModel

GenericTypesCacheKey = tuple[Any, Any, tuple[Any, ...]]

# Note: We want to remove LimitedDict, but to do this, we'd need to improve the handling of generics caching.
#   Right now, to handle recursive generics, we some types must remain cached for brief periods without references.
#   By chaining the WeakValuesDict with a LimitedDict, we have a way to retain caching for all types with references,
#   while also retaining a limited number of types even without references. This is generally enough to build
#   specific recursive generic models without losing required items out of the cache.

KT = TypeVar('KT')
VT = TypeVar('VT')
_LIMITED_DICT_SIZE = 100


class LimitedDict(dict[KT, VT]):
    def __init__(self, size_limit: int = _LIMITED_DICT_SIZE) -> None:
        self.size_limit = size_limit
        super().__init__()

    def __setitem__(self, key: KT, value: VT, /) -> None:
        super().__setitem__(key, value)
        if len(self) > self.size_limit:
            excess = len(self) - self.size_limit + self.size_limit // 10
            to_remove = list(self.keys())[:excess]
            for k in to_remove:
                del self[k]


# weak dictionaries allow the dynamically created parametrized versions of generic models to get collected
# once they are no longer referenced by the caller.
GenericTypesCache = WeakValueDictionary[GenericTypesCacheKey, 'type[BaseModel]']

if TYPE_CHECKING:

    class DeepChainMap(ChainMap[KT, VT]):  # type: ignore
        ...

else:

    class DeepChainMap(ChainMap):
        """Variant of ChainMap that allows direct updates to inner scopes.

        Taken from https://docs.python.org/3/library/collections.html#collections.ChainMap,
        with some light modifications for this use case.
        """

        def clear(self) -> None:
            for mapping in self.maps:
                mapping.clear()

        def __setitem__(self, key: KT, value: VT) -> None:
            for mapping in self.maps:
                mapping[key] = value

        def __delitem__(self, key: KT) -> None:
            hit = False
            for mapping in self.maps:
                if key in mapping:
                    del mapping[key]
                    hit = True
            if not hit:
                raise KeyError(key)


# Despite the fact that LimitedDict _seems_ no longer necessary, I'm very nervous to actually remove it
# and discover later on that we need to re-add all this infrastructure...
# _GENERIC_TYPES_CACHE = DeepChainMap(GenericTypesCache(), LimitedDict())

_GENERIC_TYPES_CACHE = GenericTypesCache()


class PydanticGenericMetadata(TypedDict):
    origin: type[BaseModel] | None  # analogous to typing._GenericAlias.__origin__
    args: tuple[Any, ...]  # analogous to typing._GenericAlias.__args__
    parameters: tuple[TypeVar, ...]  # analogous to typing.Generic.__parameters__


class PydanticGenericAlias(types.GenericAlias):
    """A generic alias representing a generic model parametrized with non-concrete arguments.

    When a generic model is parametrized and the resulting arguments still contain type variables
    (e.g. `Model[T]`, `Model[T, str]`, `Model[list[T]]`), the parametrization is represented as an
    alias (and not as a concrete class, which is only created for fully concrete parametrizations).
    This has two important benefits over the historical "concrete class everywhere" representation:

    - The arguments are preserved. `Model[T]` used to be collapsed to `Model` itself, making it
      impossible to distinguish an explicitly parametrized annotation (`fld: Model[T]`, where `T`
      must be substituted when the outer model is parametrized) from a bare one (`fld: Model`,
      where `T` is out of scope and must be left alone) — see issue #11223.
    - The alias participates in the standard typing machinery: `list[Model[T]]` correctly reports
      `(T,)` as its `__parameters__` and can be re-parametrized (`list[Model[T]][int]`), which is
      impossible when `Model[T]` is a plain class — see issue #6994.

    For backwards compatibility, operational uses of the alias (instantiation, attribute access,
    subclassing, `isinstance()`) are delegated to a lazily *materialized* concrete class, which
    is the class that `Model[args]` historically evaluated to.
    """

    # Note: `types.GenericAlias` instances are weakref-able and support subclassing.
    # `__origin__`, `__args__` and `__parameters__` are provided by the base class.

    @property
    def __pydantic_generic_metadata__(self) -> PydanticGenericMetadata:
        # Defining this as a property (instead of relying on the default attribute proxying to
        # the origin) makes the pydantic-aware `get_origin()`/`get_args()`/`iter_contained_typevars()`
        # functions work transparently on alias instances.
        return {'origin': self.__origin__, 'args': self.__args__, 'parameters': self.__parameters__}

    def _materialize(self) -> type[BaseModel]:
        """Create (or fetch) the concrete class historically associated with this parametrization."""
        return materialize_generic_parametrization(self.__origin__, self.__args__)

    def __getitem__(self, item: Any) -> Any:
        # Let `types.GenericAlias` perform the (typing-spec compliant) substitution, then
        # re-dispatch to the origin's `__class_getitem__` so that fully concrete results
        # produce a proper class:
        substituted = super().__getitem__(item)
        return self.__origin__[substituted.__args__]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._materialize()(*args, **kwargs)

    def __mro_entries__(self, bases: tuple[Any, ...]) -> tuple[type[Any], ...]:
        # Subclassing `class Sub(Model[T, str])` historically used the concrete class as the
        # actual base (with partially substituted fields); preserve that:
        return (self._materialize(),)

    def __instancecheck__(self, obj: Any) -> bool:
        return isinstance(obj, self._materialize())

    def __subclasscheck__(self, cls: type) -> bool:
        return issubclass(cls, self._materialize())

    # Attribute names always resolved on the alias itself (never proxied to the
    # materialized class). Anything dunder-like is additionally resolved through the
    # default `types.GenericAlias` behavior, except for the names in
    # `_MATERIALIZED_DUNDER_ATTRS` below:
    _MATERIALIZED_DUNDER_ATTRS: typing.ClassVar[frozenset[str]] = frozenset(
        {'__name__', '__qualname__', '__fields__'}
    )

    def __getattribute__(self, name: str) -> Any:
        # `types.GenericAlias` proxies unknown attributes to the *origin* (even the ones defined
        # on this subclass, as the C implementation is unaware of them); we proxy them to the
        # *materialized* class instead, so that e.g. `Model[T, str].model_fields` reflects the
        # (partial) parametrization, as it did when parametrization always created a class.
        if name in ('_materialize', '_MATERIALIZED_DUNDER_ATTRS', '__pydantic_generic_metadata__'):
            return object.__getattribute__(self, name)
        if name.startswith('__') and name not in PydanticGenericAlias._MATERIALIZED_DUNDER_ATTRS:
            return super().__getattribute__(name)
        return getattr(object.__getattribute__(self, '_materialize')(), name)


def create_generic_submodel(
    model_name: str,
    origin: type[BaseModel],
    args: tuple[Any, ...],
    params: tuple[Any, ...],
    creation_hook: typing.Callable[[type[BaseModel]], None] | None = None,
) -> type[BaseModel]:
    """Dynamically create a submodel of a provided (generic) BaseModel.

    This is used when producing concrete parametrizations of generic models. This function
    only *creates* the new subclass; the schema/validators/serialization must be updated to
    reflect a concrete parametrization elsewhere.

    Args:
        model_name: The name of the newly created model.
        origin: The base class for the new model to inherit from.
        args: A tuple of generic metadata arguments.
        params: A tuple of generic metadata parameters.

    Returns:
        The created submodel.
    """
    namespace: dict[str, Any] = {'__module__': origin.__module__}
    # As per https://docs.python.org/3/reference/datamodel.html#slots:
    # "The action of a __slots__ declaration is not limited to the class where it is defined.
    # __slots__ declared in parents are available in child classes. However, instances of a
    # child subclass will get a __dict__ and __weakref__ unless the subclass also defines
    # __slots__".
    # Because when users parameterize a generic model, we create a subclass of such generic model
    # (what happens in this function), they can't control the fact that no slots is defined on the
    # dynamic subclass, and so even if they defined extra __slots__ on the generic class (which results
    # in the class *not* being weakref-able), the parameterized class *will* be weakref-able.
    # For this reason (and to make Pydantic generic models behavior closer to generic aliases),
    # we forward any slots from the origin:
    if '__slots__' in origin.__dict__:
        namespace['__slots__'] = origin.__dict__['__slots__']
    bases = (origin,)
    meta, ns, kwds = prepare_class(model_name, bases)
    namespace.update(ns)
    created_model = meta(
        model_name,
        bases,
        namespace,
        __pydantic_generic_metadata__={
            'origin': origin,
            'args': args,
            'parameters': params,
        },
        __pydantic_reset_parent_namespace__=False,
        _creation_hook=creation_hook,
        **kwds,
    )

    model_module, called_globally = _get_caller_frame_info(depth=3)
    if called_globally:  # create global reference and therefore allow pickling
        object_by_reference = None
        reference_name = model_name
        reference_module_globals = sys.modules[model_module or created_model.__module__].__dict__
        while object_by_reference is not created_model:
            object_by_reference = reference_module_globals.setdefault(reference_name, created_model)
            reference_name += '_'

    return created_model


def materialize_generic_parametrization(origin: type[BaseModel], args: tuple[Any, ...]) -> type[BaseModel]:
    """Create (or fetch from cache) the concrete class for a parametrization of a generic model.

    For an identity parametrization (`Model[T]` where `(T,)` are exactly `Model`'s parameters),
    the origin itself is returned (matching the historical behavior where such parametrizations
    were collapsed to the origin class).
    """
    parameters = origin.__pydantic_generic_metadata__['parameters']
    if args == parameters:
        return origin

    cache_key = (origin, args, ('materialized', _union_orderings_key(args)))
    cached = _GENERIC_TYPES_CACHE.get(cache_key)
    if cached is not None:
        return cached

    model_name = origin.model_parametrized_name(args)
    params = tuple(dict.fromkeys(iter_contained_typevars(args)))

    def _register_in_cache(submodel: type[BaseModel]) -> None:
        _GENERIC_TYPES_CACHE[cache_key] = submodel

    return create_generic_submodel(model_name, origin, args, params, creation_hook=_register_in_cache)


def _get_caller_frame_info(depth: int = 2) -> tuple[str | None, bool]:
    """Used inside a function to check whether it was called globally.

    Args:
        depth: The depth to get the frame.

    Returns:
        A tuple contains `module_name` and `called_globally`.

    Raises:
        RuntimeError: If the function is not called inside a function.
    """
    try:
        previous_caller_frame = sys._getframe(depth)
    except ValueError as e:
        raise RuntimeError('This function must be used inside another function') from e
    except AttributeError:  # sys module does not have _getframe function, so there's nothing we can do about it
        return None, False
    frame_globals = previous_caller_frame.f_globals
    return frame_globals.get('__name__'), previous_caller_frame.f_locals is frame_globals


DictValues: type[Any] = {}.values().__class__


def iter_contained_typevars(v: Any) -> Generator[TypeVar]:
    """Recursively iterate through all subtypes and type args of `v` and yield any typevars that are found.

    This is inspired as an alternative to directly accessing the `__parameters__` attribute of a GenericAlias,
    since __parameters__ of (nested) generic BaseModel subclasses won't show up in that list.
    """
    if isinstance(v, TypeVar):
        yield v
    elif is_model_class(v):
        yield from v.__pydantic_generic_metadata__['parameters']
    elif isinstance(v, (DictValues, list)):
        for var in v:
            yield from iter_contained_typevars(var)
    else:
        args = get_args(v)
        for arg in args:
            yield from iter_contained_typevars(arg)


def get_args(v: Any) -> Any:
    pydantic_generic_metadata: PydanticGenericMetadata | None = getattr(v, '__pydantic_generic_metadata__', None)
    if pydantic_generic_metadata:
        return pydantic_generic_metadata.get('args')
    return typing_extensions.get_args(v)


def get_origin(v: Any) -> Any:
    pydantic_generic_metadata: PydanticGenericMetadata | None = getattr(v, '__pydantic_generic_metadata__', None)
    if pydantic_generic_metadata:
        return pydantic_generic_metadata.get('origin')
    return typing_extensions.get_origin(v)


def get_standard_typevars_map(cls: Any) -> dict[TypeVar, Any] | None:
    """Package a generic type's typevars and parametrization (if present) into a dictionary compatible with the
    `replace_types` function. Specifically, this works with standard typing generics and typing._GenericAlias.
    """
    origin = get_origin(cls)
    if origin is None:
        return None
    if not hasattr(origin, '__parameters__'):
        return None

    # In this case, we know that cls is a _GenericAlias, and origin is the generic type
    # So it is safe to access cls.__args__ and origin.__parameters__
    args: tuple[Any, ...] = cls.__args__  # type: ignore
    parameters: tuple[TypeVar, ...] = origin.__parameters__
    return dict(zip(parameters, args, strict=True))


def get_original_bases(cls: Any) -> tuple[Any, ...]:
    """Return the original bases of the provided class, i.e. the bases as they appear in the class definition,
    *before* `__mro_entries__` was called on them (e.g. `Foo[int]`, and not `Foo`).

    This is functionally equivalent to `types.get_original_bases` (only available in Python 3.12+), and
    is careful *not* to use plain attribute access for `__orig_bases__`, as it would return the attribute
    from a parent class if not set on the class itself.
    """
    try:
        return cls.__dict__.get('__orig_bases__', cls.__bases__)
    except AttributeError:
        return getattr(cls, '__bases__', ())


def get_composed_typevars_maps(
    tp: Any, typevars_map: Mapping[TypeVar, Any] | None = None
) -> dict[Any, dict[TypeVar, Any]]:
    """Build the typevars maps of every class in the generic inheritance chain of `tp`,
    composed transitively through the original bases of each class.

    Args:
        tp: A class or a parametrization of a generic class (i.e. a generic alias).
        typevars_map: The typevars map for `tp`'s own type parameters, if already known
            (in which case `tp` is expected to be a class). If not provided, it is inferred
            from `tp` (using `get_standard_typevars_map`).

    Returns:
        A dictionary mapping each class of the inheritance chain to the typevars map that is
        valid for the annotations *declared* on that specific class. The returned dictionary
        is ordered from the most derived class to the least derived one.

    Example:
        ```python {test="skip" lint="skip"}
        class A(Generic[T]):
            a: T

        class B(A[list[U]], Generic[U]):
            b: U

        get_composed_typevars_maps(B[int])
        #> {B: {U: int}, A: {T: list[int]}}
        ```

    Note:
        A single flat map (instead of per-class maps) would be incorrect when the same `TypeVar`
        instance has different meanings in different classes of the hierarchy, e.g. with
        `class Bar(Foo[str, T], Generic[T])`, `T` maps to `str` for annotations declared on `Foo`
        (if `Foo`'s first parameter is `T` as well), but to `Bar`'s parametrization for annotations
        declared on `Bar`.
    """
    if typevars_map is None:
        typevars_map = get_standard_typevars_map(tp)
    origin = get_origin(tp)
    cls = origin if origin is not None else tp

    maps: dict[Any, dict[TypeVar, Any]] = {}
    _compose_typevars_maps(cls, dict(typevars_map) if typevars_map else {}, maps)
    return maps


def _compose_typevars_maps(cls: Any, typevars_map: dict[TypeVar, Any], maps: dict[Any, dict[TypeVar, Any]]) -> None:
    """Recursively compose `typevars_map` (the map valid for `cls`) with the parametrization
    of each of `cls`'s original bases, populating `maps`.
    """
    if cls in maps:
        # The class was already visited from a more derived parametrization
        # (e.g. diamond inheritance), which takes priority:
        return
    maps[cls] = typevars_map

    for base in get_original_bases(cls):
        base_origin = typing_extensions.get_origin(base)
        if base_origin is None:
            if isinstance(base, type) and base is not object:
                # A plain (non-subscripted) base class. If it is a generic class, its type
                # parameters are shared with `cls` (e.g. with `class B(A): ...`, `B[int]`
                # parametrizes `A`'s type parameters as well), so the relevant entries of
                # the current map are propagated:
                base_params: tuple[TypeVar, ...] = getattr(base, '__parameters__', ())
                base_map = {p: typevars_map[p] for p in base_params if p in typevars_map}
                _compose_typevars_maps(base, base_map, maps)
        elif base_origin is typing.Generic:
            # `Generic[T]` only declares the type parameters of `cls`, nothing to compose:
            continue
        else:
            parameters: tuple[TypeVar, ...] | None = getattr(base_origin, '__parameters__', None)
            if parameters:
                # Substitute the base's arguments with the current map, e.g. for `B(A[list[U]])`
                # with a map of `{U: int}`, `A`'s map becomes `{T: list[int]}`:
                args = tuple(replace_types(arg, typevars_map) for arg in typing_extensions.get_args(base))
                # Be lenient regarding a length mismatch, which can happen with `TypeVarTuple`
                # or PEP 696 defaults (in which case substitution is best effort):
                base_map = dict(zip(parameters, args, strict=False))
            else:
                base_map = {}
            _compose_typevars_maps(base_origin, base_map, maps)


def get_model_typevars_map(cls: type[BaseModel]) -> dict[TypeVar, Any]:
    """Package a generic BaseModel's typevars and concrete parametrization (if present) into a dictionary compatible
    with the `replace_types` function.

    Since BaseModel.__class_getitem__ does not produce a typing._GenericAlias, and the BaseModel generic info is
    stored in the __pydantic_generic_metadata__ attribute, we need special handling here.
    """
    # TODO: This could be unified with `get_standard_typevars_map` if we stored the generic metadata
    #   in the __origin__, __args__, and __parameters__ attributes of the model.
    generic_metadata = cls.__pydantic_generic_metadata__
    origin = generic_metadata['origin']
    args = generic_metadata['args']
    if not args:
        # No need to go into `iter_contained_typevars`:
        return {}
    return dict(zip(iter_contained_typevars(origin), args, strict=True))


def replace_types(type_: Any, type_map: Mapping[TypeVar, Any] | None) -> Any:
    """Return type with all occurrences of `type_map` keys recursively replaced with their values.

    Args:
        type_: The class or generic alias.
        type_map: Mapping from `TypeVar` instance to concrete types.

    Returns:
        A new type representing the basic structure of `type_` with all
        `typevar_map` keys recursively replaced.

    Example:
        ```python
        from pydantic._internal._generics import replace_types

        replace_types(tuple[str, list[str] | float], {str: int})
        #> tuple[int, list[int] | float]
        ```
    """
    if not type_map:
        return type_

    type_args = get_args(type_)
    origin_type = get_origin(type_)

    if typing_objects.is_annotated(origin_type):
        annotated_type, *annotations = type_args
        annotated_type = replace_types(annotated_type, type_map)
        # TODO remove parentheses when we drop support for Python 3.10:
        return Annotated[(annotated_type, *annotations)]

    # Having type args is a good indicator that this is a typing special form
    # instance or a generic alias of some sort.
    if type_args:
        resolved_type_args = tuple(replace_types(arg, type_map) for arg in type_args)
        if all_identical(type_args, resolved_type_args):
            # If all arguments are the same, there is no need to modify the
            # type or create a new object at all
            return type_

        if (
            origin_type is not None
            and isinstance(type_, _typing_extra.typing_base)
            and not isinstance(origin_type, _typing_extra.typing_base)
            and getattr(type_, '_name', None) is not None
        ):
            # In python < 3.9 generic aliases don't exist so any of these like `list`,
            # `type` or `collections.abc.Callable` need to be translated.
            # See: https://www.python.org/dev/peps/pep-0585
            origin_type = getattr(typing, type_._name)
        assert origin_type is not None

        if is_union_origin(origin_type):
            if any(typing_objects.is_any(arg) for arg in resolved_type_args):
                # `Any | T` ~ `Any`:
                resolved_type_args = (Any,)
            # `Never | T` ~ `T`:
            resolved_type_args = tuple(
                arg
                for arg in resolved_type_args
                if not (typing_objects.is_noreturn(arg) or typing_objects.is_never(arg))
            )

        # PEP-604 syntax (e.g. `list | str`) is represented with a types.UnionType object that does not
        # implement `__getitem__()`. In Python 3.14+, `typing.Union` and `types.UnionType` are the same,
        # and we instead rely on `typing.Union` as it implicitly converts string annotations to `ForwardRef`
        # instances (this is to avoid type errors as per https://github.com/python/cpython/pull/105366).
        if sys.version_info < (3, 14) and origin_type is types.UnionType:
            return reduce(operator.or_, resolved_type_args)
        # NotRequired[T] and Required[T] don't support tuple type resolved_type_args, hence the condition below
        return origin_type[resolved_type_args[0] if len(resolved_type_args) == 1 else resolved_type_args]

    # Note: a *bare* generic model class (with unfilled parameters) is deliberately left
    # untouched: per the typing spec, its type variables are out of scope of the current
    # substitution (see https://github.com/pydantic/pydantic/issues/11223). Explicitly
    # parametrized models (`Model[T]`) are represented as `PydanticGenericAlias` instances
    # and handled by the generic-alias branch above.

    # Handle special case for typehints that can have lists as arguments.
    # `typing.Callable[[int, str], int]` is an example for this.
    if isinstance(type_, list):
        resolved_list = [replace_types(element, type_map) for element in type_]
        if all_identical(type_, resolved_list):
            return type_
        return resolved_list

    # If all else fails, we try to resolve the type directly and otherwise just
    # return the input with no modifications.
    return type_map.get(type_, type_)


def map_generic_model_arguments(cls: type[BaseModel], args: tuple[Any, ...]) -> dict[TypeVar, Any]:
    """Return a mapping between the parameters of a generic model and the provided arguments during parameterization.

    Raises:
        TypeError: If the number of arguments does not match the parameters (i.e. if providing too few or too many arguments).

    Example:
        ```python {test="skip" lint="skip"}
        class Model[T, U, V = int](BaseModel): ...

        map_generic_model_arguments(Model, (str, bytes))
        #> {T: str, U: bytes, V: int}

        map_generic_model_arguments(Model, (str,))
        #> TypeError: Too few arguments for <class '__main__.Model'>; actual 1, expected at least 2

        map_generic_model_arguments(Model, (str, bytes, int, complex))
        #> TypeError: Too many arguments for <class '__main__.Model'>; actual 4, expected 3
        ```

    Note:
        This function is analogous to the private `typing._check_generic_specialization` function.
    """
    parameters = cls.__pydantic_generic_metadata__['parameters']
    expected_len = len(parameters)
    typevars_map: dict[TypeVar, Any] = {}

    _missing = object()
    for parameter, argument in zip_longest(parameters, args, fillvalue=_missing):
        if parameter is _missing:
            raise TypeError(f'Too many arguments for {cls}; actual {len(args)}, expected {expected_len}')

        if argument is _missing:
            param = cast(TypeVar, parameter)
            try:
                has_default = param.has_default()  # pyright: ignore[reportAttributeAccessIssue]
            except AttributeError:
                # Happens if using `typing.TypeVar` (and not `typing_extensions`) on Python < 3.13.
                has_default = False
            if has_default:
                # The default might refer to other type parameters. For an example, see:
                # https://typing.python.org/en/latest/spec/generics.html#type-parameters-as-parameters-to-generics
                typevars_map[param] = replace_types(param.__default__, typevars_map)  # pyright: ignore[reportAttributeAccessIssue]
            else:
                expected_len -= sum(hasattr(p, 'has_default') and p.has_default() for p in parameters)  # pyright: ignore[reportAttributeAccessIssue]
                raise TypeError(f'Too few arguments for {cls}; actual {len(args)}, expected at least {expected_len}')
        else:
            param = cast(TypeVar, parameter)
            _check_typevar_argument(cls, param, argument)
            typevars_map[param] = argument

    return typevars_map


def _check_typevar_argument(cls: type[BaseModel], param: TypeVar, argument: Any) -> None:
    """Best-effort validation of a parametrization argument against the type variable's upper bound or constraints.

    The check is lenient: it only fails when we can confidently tell the argument is invalid
    (both the argument and the bound/constraints are runtime-checkable classes). Type checkers
    already flag invalid parametrizations statically; this runtime check catches the cases from
    https://github.com/pydantic/pydantic/issues/7703 where an invalid parametrization would
    otherwise silently produce a model validating against the wrong type.
    """
    if isinstance(argument, typing.TypeVar) or typing_objects.is_any(argument):
        # Rebinding to another type variable (or explicit `Any`) is always allowed:
        return

    if param.__constraints__:
        for constraint in param.__constraints__:
            if argument is constraint:
                return
            if isinstance(argument, type) and isinstance(constraint, type):
                try:
                    if issubclass(argument, constraint):
                        return
                except TypeError:  # pragma: no cover
                    return  # non-runtime-checkable constraint, be lenient
            else:
                # At least one constraint (or the argument) isn't a plain class
                # (e.g. a parametrized generic or special form) — be lenient:
                return
        raise TypeError(
            f'{argument!r} is not a valid parametrization of {param!r} in {cls.__name__!r}; '
            f'it must be one of: {", ".join(repr(c) for c in param.__constraints__)}'
        )

    bound = param.__bound__
    if bound is not None and isinstance(bound, type) and isinstance(argument, type):
        try:
            valid = issubclass(argument, bound)
        except TypeError:  # pragma: no cover
            return  # non-runtime-checkable bound, be lenient
        if not valid:
            raise TypeError(
                f'{argument!r} is not a valid parametrization of {param!r} in {cls.__name__!r}; '
                f'it must be a subclass of {bound!r}'
            )


_generic_recursion_cache: ContextVar[set[str] | None] = ContextVar('_generic_recursion_cache', default=None)

_in_flight_origin_rebuilds: ContextVar[set[int] | None] = ContextVar('_in_flight_origin_rebuilds', default=None)


@contextmanager
def origin_rebuild_guard(origin: type[BaseModel]) -> Iterator[bool]:
    """Guard against reentrant rebuilds of a generic origin model during parametrization.

    `BaseModel.__class_getitem__()` attempts to rebuild the generic origin before creating the
    parametrized class (so that newly defined types are taken into account). If evaluating an
    annotation during that rebuild recursively parametrizes the same origin, attempting the
    origin rebuild again would recurse forever. Yields `True` if the origin rebuild can proceed
    (i.e. it is not already being rebuilt higher up in the stack), `False` otherwise.
    """
    in_flight = _in_flight_origin_rebuilds.get()
    token = None
    if in_flight is None:
        in_flight = set()
        token = _in_flight_origin_rebuilds.set(in_flight)

    key = id(origin)
    try:
        if key in in_flight:
            yield False
        else:
            in_flight.add(key)
            try:
                yield True
            finally:
                in_flight.discard(key)
    finally:
        if token is not None:
            _in_flight_origin_rebuilds.reset(token)


@contextmanager
def generic_recursion_self_type(
    origin: type[BaseModel], args: tuple[Any, ...]
) -> Generator[PydanticRecursiveRef | None]:
    """This contextmanager should be placed around the recursive calls used to build a generic type,
    and accept as arguments the generic origin type and the type arguments being passed to it.

    If the same origin and arguments are observed twice, it implies that a self-reference placeholder
    can be used while building the core schema, and will produce a schema_ref that will be valid in the
    final parent schema.
    """
    previously_seen_type_refs = _generic_recursion_cache.get()
    if previously_seen_type_refs is None:
        previously_seen_type_refs = set()
        token = _generic_recursion_cache.set(previously_seen_type_refs)
    else:
        token = None

    try:
        type_ref = get_type_ref(origin, args_override=args)
        if type_ref in previously_seen_type_refs:
            self_type = PydanticRecursiveRef(type_ref=type_ref)
            yield self_type
        else:
            previously_seen_type_refs.add(type_ref)
            yield
            previously_seen_type_refs.remove(type_ref)
    finally:
        if token:
            _generic_recursion_cache.reset(token)


def recursively_defined_type_refs() -> set[str]:
    visited = _generic_recursion_cache.get()
    if not visited:
        return set()  # not in a generic recursion, so there are no types

    return visited.copy()  # don't allow modifications


def _generic_cache_get(key: GenericTypesCacheKey) -> type[BaseModel] | None:
    try:
        return _GENERIC_TYPES_CACHE.get(key)
    except TypeError:  # unhashable typevar values
        return None


def _generic_cache_set(key: GenericTypesCacheKey, value: type[BaseModel]) -> None:
    try:
        _GENERIC_TYPES_CACHE[key] = value
    except TypeError:  # unhashable typevar values
        pass


def get_cached_generic_type_early(parent: type[BaseModel], typevar_values: Any) -> type[BaseModel] | None:
    """The use of a two-stage cache lookup approach was necessary to have the highest performance possible for
    repeated calls to `__class_getitem__` on generic types (which may happen in tighter loops during runtime),
    while still ensuring that certain alternative parametrizations ultimately resolve to the same type.

    As a concrete example, this approach was necessary to make Model[List[T]][int] equal to Model[List[int]].
    The approach could be modified to not use two different cache keys at different points, but the
    _early_cache_key is optimized to be as quick to compute as possible (for repeated-access speed), and the
    _late_cache_key is optimized to be as "correct" as possible, so that two types that will ultimately be the
    same after resolving the type arguments will always produce cache hits.

    If we wanted to move to only using a single cache key per type, we would either need to always use the
    slower/more computationally intensive logic associated with _late_cache_key, or would need to accept
    that Model[List[T]][int] is a different type than Model[List[T]][int]. Because we rely on subclass relationships
    during validation, I think it is worthwhile to ensure that types that are functionally equivalent are actually
    equal.
    """
    return _generic_cache_get(_early_cache_key(parent, typevar_values))


def get_cached_generic_type_late(
    parent: type[BaseModel], typevar_values: Any, origin: type[BaseModel], args: tuple[Any, ...]
) -> type[BaseModel] | None:
    """See the docstring of `get_cached_generic_type_early` for more information about the two-stage cache lookup."""
    cached = _generic_cache_get(_late_cache_key(origin, args, typevar_values))
    if cached is not None:
        set_cached_generic_type(parent, typevar_values, cached, origin, args)
    return cached


def set_cached_generic_type(
    parent: type[BaseModel],
    typevar_values: tuple[Any, ...],
    type_: type[BaseModel],
    origin: type[BaseModel] | None = None,
    args: tuple[Any, ...] | None = None,
) -> None:
    """See the docstring of `get_cached_generic_type_early` for more information about why items are cached with
    two different keys.
    """
    _generic_cache_set(_early_cache_key(parent, typevar_values), type_)
    if len(typevar_values) == 1:
        _generic_cache_set(_early_cache_key(parent, typevar_values[0]), type_)
    if origin and args:
        _generic_cache_set(_late_cache_key(origin, args, typevar_values), type_)


def drop_cached_generic_type(
    parent: type[BaseModel],
    typevar_values: tuple[Any, ...],
    origin: type[BaseModel] | None = None,
    args: tuple[Any, ...] | None = None,
) -> None:
    """Remove the cache entries registered by `set_cached_generic_type`.

    Used to avoid leaving partially-built classes in the cache if parametrization fails.
    """
    _GENERIC_TYPES_CACHE.pop(_early_cache_key(parent, typevar_values), None)
    if len(typevar_values) == 1:
        _GENERIC_TYPES_CACHE.pop(_early_cache_key(parent, typevar_values[0]), None)
    if origin and args:
        _GENERIC_TYPES_CACHE.pop(_late_cache_key(origin, args, typevar_values), None)


def _union_orderings_key(typevar_values: Any) -> Any:
    """This is intended to help differentiate between Union types with the same arguments in different order.

    Thanks to caching internal to the `typing` module, it is not possible to distinguish between
    List[Union[int, float]] and List[Union[float, int]] (and similarly for other "parent" origins besides List)
    because `typing` considers Union[int, float] to be equal to Union[float, int].

    However, you _can_ distinguish between (top-level) Union[int, float] vs. Union[float, int].
    Because we parse items as the first Union type that is successful, we get slightly more consistent behavior
    if we make an effort to distinguish the ordering of items in a union. It would be best if we could _always_
    get the exact-correct order of items in the union, but that would require a change to the `typing` module itself.
    (See https://github.com/python/cpython/issues/86483 for reference.)
    """
    if isinstance(typevar_values, tuple):
        return tuple(_union_orderings_key(value) for value in typevar_values)
    elif typing_objects.is_union(typing_extensions.get_origin(typevar_values)):
        return get_args(typevar_values)
    else:
        return ()


def _early_cache_key(cls: type[BaseModel], typevar_values: Any) -> GenericTypesCacheKey:
    """This is intended for minimal computational overhead during lookups of cached types.

    Note that this is overly simplistic, and it's possible that two different cls/typevar_values
    inputs would ultimately result in the same type being created in BaseModel.__class_getitem__.
    To handle this, we have a fallback _late_cache_key that is checked later if the _early_cache_key
    lookup fails, and should result in a cache hit _precisely_ when the inputs to __class_getitem__
    would result in the same type.
    """
    return cls, typevar_values, _union_orderings_key(typevar_values)


def _late_cache_key(origin: type[BaseModel], args: tuple[Any, ...], typevar_values: Any) -> GenericTypesCacheKey:
    """This is intended for use later in the process of creating a new type, when we have more information
    about the exact args that will be passed. If it turns out that a different set of inputs to
    __class_getitem__ resulted in the same inputs to the generic type creation process, we can still
    return the cached type, and update the cache with the _early_cache_key as well.
    """
    # The _union_orderings_key is placed at the start here to ensure there cannot be a collision with an
    # _early_cache_key, as that function will always produce a BaseModel subclass as the first item in the key,
    # whereas this function will always produce a tuple as the first item in the key.
    return _union_orderings_key(typevar_values), origin, args
