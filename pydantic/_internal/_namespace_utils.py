from __future__ import annotations

import sys
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from functools import cached_property
from typing import Any, Iterator, NamedTuple, TypeAlias, TypeVar

GlobalsNamespace: TypeAlias = dict[str, Any]
"""A global namespace.

In most cases, this is a reference to the `__dict__` attribute of a module.
This namespace type is expected as the `globals` argument during annotations evaluation.
"""

MappingNamespace: TypeAlias = Mapping[str, Any]
"""Any kind of namespace.

In most cases, this is a local namespace (e.g. the `__dict__` attribute of a class,
the [`f_locals`][frame.f_locals] attribute of a frame object).
This namespace type is expected as the `locals` argument during annotations evaluation.
"""


class NamespacesTuple(NamedTuple):
    """A tuple of globals and locals to be used during annotations evaluation.

    This datastructure is defined as a named tuple so that it can easily be unpacked:

    ```python lint="skip" test="skip"
    def eval_type(typ: type[Any], ns: NamespacesTuple) -> None:
        return eval(typ, *ns)
    ```
    """

    globals: GlobalsNamespace
    """The namespace to be used as the `globals` argument during annotations evaluation."""

    locals: MappingNamespace
    """The namespace to be used as the `locals` argument during annotations evaluation."""


def get_module_ns_of(obj: Any) -> dict[str, Any]:
    """Get the namespace of the module where the object is defined.

    Caution: this function does not return a copy of the module namespace, so it should not be mutated.
    The burden of enforcing this is on the caller.
    """
    module_name = getattr(obj, '__module__', None)
    if module_name:
        try:
            return sys.modules[module_name].__dict__
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            return {}
    return {}


class LazyLocalNamespace(Mapping[str, Any]):
    """A lazily evaluated mapping, to be used as the `locals` argument during annotations evaluation.

    While the [`eval`][eval] function expects a mapping as the `locals` argument, it only
    performs `__getitem__` calls. The [`Mapping`][collections.abc.Mapping] abstract base class
    is fully implemented only for type checking purposes.

    Args:
        *namespaces: The namespaces to consider, in ascending order of priority.

    Example:
        ```python lint="skip" test="skip"
        ns = LazyLocalNamespace({'a': 1, 'b': 2}, {'a': 3})
        ns['a']
        #> 3
        ns['b']
        #> 2
        ```
    """

    def __init__(self, *namespaces: MappingNamespace) -> None:
        self._namespaces = namespaces

    @cached_property
    def data(self) -> Mapping[str, Any]:
        return {k: v for ns in self._namespaces for k, v in ns.items()}

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: object) -> bool:
        return key in self.data

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)


# This function is quite similar to the `NsResolver.types_namespace` property, but it also
# handles functions, while `NsResolver` only deals with type objects. This function should
# thus only be used when you want to resolve annotations for an object when *not* in a
# core schema generation context:
def ns_from(obj: Any, parent_namespace: MappingNamespace | None = None) -> NamespacesTuple:
    """Return the global and local namespaces to be used when evaluating annotations for the provided object.

    The global namespace will be the `__dict__` attribute of the module the object was defined in. The
    local namespace will be constructed depending on the object type:
    - if it is a type object, use the object's `__dict__` attribute and add the object itself to the locals.
    - if it is a function, add the `__type_params__` introduced by PEP 695.

    Args:
        obj: The object to use when building namespaces.
        parent_namespace: Optional namespace to be added with the lowest priority in the local namespace.
    """
    locals_list: list[MappingNamespace] = []
    if parent_namespace is not None:
        locals_list.append(parent_namespace)

    global_ns = get_module_ns_of(obj)

    if isinstance(obj, type):
        locals_list.extend(
            [
                vars(obj),  # i.e. `obj.__dict__`
                {obj.__name__: obj},
            ]
        )
    else:
        # For functions, get the `__type_params__` attribute introduced by PEP 695.
        # Note that the typing `_eval_type` function expects type params to be
        # passed as a separate argument. However, internally, `_eval_type` calls
        # `ForwardRef._evaluate` which will merge type params with the localns,
        # essentially mimicing what we do here.
        type_params: tuple[TypeVar, ...] = ()
        if parent_namespace is not None:
            # We also fetch type params from the parent namespace. If present, it probably
            # means the function was defined in a class. This is to support the following:
            # https://github.com/python/cpython/issues/124089.
            type_params += parent_namespace.get('__type_params__', ())
        type_params += getattr(obj, '__type_params__', ())
        locals_list.append({t.__name__: t for t in type_params})

    return NamespacesTuple(global_ns, LazyLocalNamespace(*locals_list))


class NsResolver:
    """A class holding the logic to resolve namespaces for annotations evaluation in the context
    of core schema generation.

    This class handles the namespace logic when evaluating annotations that failed to
    resolve during the initial inspection/building of the Pydantic model, dataclass, etc.

    It holds a stack of classes that are being inspected during the core schema building,
    and the `types_namespace` property exposes the globals and locals to be used for
    type annotation evaluation. Additionally -- if no class is present in the stack -- a
    fallback globals and locals can be provided with the `namespaces_tuple` argument.

    This is only meant to be used alongside with the `GenerateSchema` class.

    Args:
        namespaces_tuple: The default globals and locals to used if no class is present
            on the stack. This can be useful when using the `GenerateSchema` class
            with `TypeAdapter`, where the "type" being analyzed is a simple annotation.
        fallback_namespace: A namespace to use as a last resort if a name wasn't found
            in the locals nor the globals. This is mainly used when rebuilding a core
            schema for a Pydantic model or dataclass, where the parent namespace is used.
        override_namespace: A namespace to use first when resolving forward annotations.
            This is mainly used when rebuilding a core schema for a Pydantic model or
            dataclass, where an explicit namespace can be provided to resolve annotations
            that failed to resolve during the initial schema building.

    Example:
        ```python lint="skip" test="skip"
        ns_resolver = NsResolver(
            namespaces_tuple=NamespacesTuple({'my_global': 1}, {}),
            fallback_namespace={'fallback': 2, 'my_global': 3},
        )

        ns_resolver.types_namespace
        #> NamespacesTuple({'my_global': 1}, {})


        class MyType:
            some_local = 4


        with ns_resolver.push(MyType):
            ns_resolver.types_namespace
            #> NamespacesTuple({'my_global': 1, 'fallback': 2}, {'some_local': 4})
        ```
    """

    def __init__(
        self,
        namespaces_tuple: NamespacesTuple | None = None,
        fallback_namespace: MappingNamespace | None = None,
        override_namespace: MappingNamespace | None = None,
    ) -> None:
        self._base_ns_tuple = namespaces_tuple or NamespacesTuple({}, {})
        self._fallback_ns = fallback_namespace
        self._override_ns = override_namespace
        self._types_stack: list[type[Any]] = []

    @cached_property
    def types_namespace(self) -> NamespacesTuple:
        """The current global and local namespaces to be used for annotations evaluation."""
        if not self._types_stack:
            # TODO do we want to merge fallback and override ns here?
            return self._base_ns_tuple

        typ = self._types_stack[-1]

        globalns = get_module_ns_of(typ)
        # TODO check len(self._types_stack) == 1? As we specified,
        # fallback_namespace should only be used for the class being rebuilt.
        # However, it might be good to keep this for now to avoid having too
        # many breaking changes.
        if self._fallback_ns is not None:
            globalns = {**self._fallback_ns, **globalns}

        locals_list: list[MappingNamespace] = [vars(typ), {typ.__name__: typ}]
        if self._override_ns is not None:
            locals_list.append(self._override_ns)

        return NamespacesTuple(globalns, LazyLocalNamespace(*locals_list))

    @contextmanager
    def push(self, typ: type[Any], /) -> Generator[None]:
        """Push a type to the stack."""
        self._types_stack.append(typ)
        # Reset the cached property:
        self.__dict__.pop('types_namespace', None)
        try:
            yield
        finally:
            self._types_stack.pop()
            self.__dict__.pop('types_namespace', None)
