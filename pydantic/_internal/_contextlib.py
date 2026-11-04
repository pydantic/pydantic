"""A lightweight implementation of `@contextlib.contextmanager`."""

from __future__ import annotations

from collections.abc import Callable, Generator, Iterator
from functools import wraps
from types import TracebackType
from typing import Generic, ParamSpec, TypeVar

_T = TypeVar('_T')
_P = ParamSpec('_P')


class _GeneratorContextManager(Generic[_T]):
    """A lighter version of `contextlib._GeneratorContextManager`.

    Unlike the standard library implementation, it can't be used as a decorator or be recreated.
    This avoids storing the generator function and its arguments on each call.
    """

    __slots__ = ('gen',)

    def __init__(self, gen: Generator[_T]) -> None:
        self.gen = gen

    def __enter__(self) -> _T:
        # Faster than `next(self.gen)` (see https://github.com/python/cpython/pull/141275):
        for value in self.gen:
            return value
        raise RuntimeError("generator didn't yield")  # pragma: no cover

    def __exit__(
        self, typ: type[BaseException] | None, value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:  # Same return type as `contextlib`, so that type checkers don't assume exceptions are suppressed
        if typ is None:
            # Faster than calling `next(self.gen)` and checking for `StopIteration`:
            for _ in self.gen:
                try:  # pragma: no cover
                    raise RuntimeError("generator didn't stop")
                finally:
                    self.gen.close()  # pragma: no cover
            return False

        # Same logic as `contextlib._GeneratorContextManager.__exit__()`:
        if value is None:
            # Need to force instantiation so we can reliably tell if we get the same exception back:
            value = typ()  # pragma: no cover
        try:
            self.gen.throw(value)
        except StopIteration as exc:
            # Suppress `StopIteration` *unless* it's the same exception that was passed to `throw()`:
            return exc is not value  # pragma: no cover
        except RuntimeError as exc:
            # Don't re-raise the passed in exception:
            if exc is value:
                exc.__traceback__ = traceback
                return False
            # Avoid suppressing if a `StopIteration` exception was passed to `throw()` and later
            # wrapped into a `RuntimeError` (see PEP 479 for sync generators):
            if isinstance(value, StopIteration) and exc.__cause__ is value:  # pragma: no cover
                value.__traceback__ = traceback
                return False
            raise  # pragma: no cover
        except BaseException as exc:
            # Only re-raise if it's *not* the exception that was passed to `throw()`, because
            # `__exit__()` must not raise an exception unless `__exit__()` itself failed:
            if exc is not value:
                raise  # pragma: no cover
            exc.__traceback__ = traceback
            return False
        try:  # pragma: no cover
            raise RuntimeError("generator didn't stop after throw()")
        finally:
            self.gen.close()  # pragma: no cover


def contextmanager(func: Callable[_P, Iterator[_T]]) -> Callable[_P, _GeneratorContextManager[_T]]:
    """A lightweight replacement for `contextlib.contextmanager`, only usable in `with` statements."""

    @wraps(func)
    def helper(*args: _P.args, **kwargs: _P.kwargs) -> _GeneratorContextManager[_T]:
        return _GeneratorContextManager(func(*args, **kwargs))  # pyright: ignore[reportArgumentType]

    return helper
