from __future__ import annotations as _annotations

import itertools
import sys
from contextlib import contextmanager
from functools import cached_property
from types import ModuleType
from typing import Any, Callable, Iterator, Mapping, Type, Union

from typing_extensions import Self

ModuleSource = Union[Type[Any], Callable]


class NsResolver(Mapping[str, Any]):
    """Protects namespaces from modifications and provides a way to merge namespaces without copying namespaces."""

    def __init__(self, *, globalns: Mapping[str, Any] | ModuleSource | None = None) -> None:
        """Create namespace resolver.
        Provided global namespace is the least prioritized namespace. It is also used for Python evals globals.
        """
        globalns_dict = NsResolver._get_namespace_dict(globalns)
        self._globalns: list[Mapping[str, Any]] = [globalns_dict] if globalns_dict else []
        self._localns: list[Mapping[str, Any]] = []

    def add_localns(self, namespace: Mapping[str, Any] | ModuleSource | Self | None) -> Self:
        """Add local namespace to the resolved namespaces. Local namespace has the highest priority."""
        if isinstance(namespace, NsResolver):
            ns_dicts = namespace._localns
        else:
            localns = self._get_namespace_dict(namespace)
            ns_dicts = [localns] if localns else None
        if ns_dicts:
            self._localns.extend(ns_dicts)
            self._reset_resolved_localns()
        return self

    def current_globals(self) -> Mapping[str, Any] | None:
        """Get current global namespace. Use for Python evals. Caller must not mutate contents of this"""
        # Do not do any merging of namespaces here. Something else is wrong if any merging is done here
        return self._globalns[-1] if self._globalns else None

    @contextmanager
    def push_globalns(self, from_type: ModuleSource):
        """Push global namespace from_type as part of resolved namespaces"""
        namespace = self._module_namespace_from(from_type)
        if namespace:
            self._globalns.append(namespace)
        try:
            yield
        finally:
            if namespace:
                self._globalns.pop()

    @contextmanager
    def push_localns(self, from_type: ModuleSource):
        """Push local namespace of from_type as part of resolved namespaces"""
        namespace = self._module_namespace_from(from_type)
        if namespace:
            self._localns.append(namespace)
            self._reset_resolved_localns()
        try:
            yield
        finally:
            if namespace:
                self._localns.pop()
                self._reset_resolved_localns()

    @classmethod
    def _get_namespace_dict(cls, obj: ModuleSource | Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        if obj is None:
            return None
        elif isinstance(obj, Mapping):
            return obj if obj else None
        else:
            return cls._module_namespace_from(obj)

    @classmethod
    def _module_namespace_from(cls, obj: ModuleSource | None) -> Mapping[str, Any] | None:
        """Gets namespace mapping of module where the object is defined. Caller is expected to not mutate contents."""
        module = cls._get_module(obj)
        return module.__dict__ if module else None

    @classmethod
    def _get_module(cls, obj: type[Any] | Callable | None) -> ModuleType | None:
        module_name = getattr(obj, '__module__', None) if obj is not None else None
        if module_name:
            try:
                return sys.modules[module_name]
            except KeyError:
                # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
                pass
        return None

    def _reset_resolved_localns(self) -> None:
        self.__dict__.pop('resolved_localns', None)  # reset the cached_property

    def resolve_name(self, name: str) -> Any:
        """Resolve name in the namespaces in order."""
        for ns in reversed(self._localns):
            if name in ns:
                return ns[name]

        if (globalns := self.current_globals()) and name in globalns:
            return globalns[name]

        raise KeyError(name)

    @cached_property
    def resolved_localns(self) -> dict[str, Any]:
        """Resolves the local namespaces in order by merging them together.
        Maybe resource intensive for big namespaces. Therefore, this is only used when really needed.
        Caller is expected to not mutate contents.
        """
        return {k: v for ns in self._localns for k, v in ns.items()}

    def __getitem__(self, name: str) -> Any:  # Called by "eval" inside typing._eval_type
        return self.resolve_name(name)

    def __contains__(self, name: Any) -> bool:
        return name in (self.current_globals() or {}) or any(name in ns for ns in self._localns)

    def __iter__(self) -> Iterator[str]:
        seen: set[str] = set()
        for ns in itertools.chain(reversed(self._localns), [self.current_globals() or {}]):
            for name in ns.keys():
                if name not in seen:
                    seen.add(name)
                    yield name

    def __bool__(self) -> bool:
        return bool(self._localns) or bool(self.current_globals())

    def __len__(self) -> int:
        keys: set[str] = {*(self.current_globals() or {}).keys()}
        for ns in self._localns:
            keys.update(ns.keys())
        return len(keys)
