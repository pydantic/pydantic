import sys
from typing import Any


class DeferredDataclassMeta(type):
    def __new__(mcs, *args, **kwargs):
        original_cls = kwargs.pop('original_cls')
        frozen = kwargs.pop('frozen', False)
        slots = kwargs.pop('slots', True)
        cls = super().__new__(mcs, *args, **kwargs)
        cls._original_cls = original_cls
        cls._frozen = frozen
        cls._slots = slots
        cls._dc = None
        return cls

    def _create_dc(self):
        if self._dc is None:
            import dataclasses

            if sys.version_info >= (3, 10):
                dc_func = dataclasses.dataclass(slots=self._slots, frozen=self._frozen)
            else:
                dc_func = dataclasses.dataclass(frozen=self._frozen)
            self._dc = dc_func(self._original_cls)
            print(f'This should not be called {self._dc}')
        return self._dc

    @property
    def __dataclass_fields__(cls):
        dc = cls._create_dc()
        return dc.__dataclass_fields__

    @property
    def __dataclass_params__(self):
        dc = self._create_dc()
        return dc.__dataclass_params__

    def __getitem__(self, item):
        dc = self._create_dc()
        return dc.__class_getitem__(item)

    def __getattr__(self, item):
        dc = self._create_dc()
        return getattr(dc, item)

    def __instancecheck__(self, instance):
        dc = self._create_dc()
        return isinstance(instance, dc)

    @property
    def __name__(self):
        print('name', id(self))
        dc = self._create_dc()
        return dc.__name__


def deferred_dataclass(__cls: type[Any] = None, *, slots=True, frozen=False):
    """
    A decorator that creates a class that looks and smells very like a dataclass, but defers import of
    `dataclasses`.

    For internal use only.
    """
    if __cls is None:
        return lambda __cls: deferred_dataclass(__cls, frozen=frozen)
    else:
        class DeferredDataclass(metaclass=DeferredDataclassMeta, original_cls=__cls):
            def __new__(cls, *args, **kwargs):
                dc = cls._create_dc()
                # debug(cls, args, kwargs, dc)
                return dc(*args, **kwargs)

            def __init_subclass__(cls, **kwargs):
                raise TypeError('Inheritance of deferred dataclasses is not supported')
        return DeferredDataclass
