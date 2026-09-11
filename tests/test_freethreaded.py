import sys
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from typing_extensions import TypedDict

import pydantic.dataclasses
from pydantic import BaseModel, TypeAdapter, field_validator

from .conftest import is_free_threaded

pytestmark = [
    pytest.mark.skipif(sys.platform == 'emscripten', reason='no threading on emscripten'),
    pytest.mark.skipif(not is_free_threaded, reason='only relevant on free-threaded builds'),
]


def run_concurrently(
    setup: Callable[[], Any], target: Callable[[Any, int], Any], *, rounds: int = 100, threads: int = 8
):
    """Run `target` in `threads` threads at once, `rounds` times, with a fresh `setup()` result each round."""
    for _ in range(rounds):
        ctx = setup()
        barrier = threading.Barrier(threads)

        def work(index: int) -> None:
            barrier.wait()
            target(ctx, index)

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for future in [executor.submit(work, i) for i in range(threads)]:
                future.result()


def test_typed_dict_concurrent_type_adapter() -> None:
    def setup():
        class Record(TypedDict):
            value: int

        return Record

    def target(Record, _):
        assert TypeAdapter(Record).validate_python({'value': '42'}) == {'value': 42}

    run_concurrently(setup, target)


def test_base_model_concurrent_creation_with_shared_base() -> None:
    def setup():
        class Mixin:
            a: int = 1

            @field_validator('a')
            @classmethod
            def val_a_1(cls, v: int) -> int:
                return v

            @field_validator('a')
            @classmethod
            def val_a_2(cls, v: int) -> int:
                return v

            @field_validator('a')
            @classmethod
            def val_a_3(cls, v: int) -> int:
                return v

        return Mixin

    def target(Mixin, _):
        class Model(BaseModel, Mixin):
            b: int

        assert Model(b='1').b == 1

    run_concurrently(setup, target)


def test_dataclass_concurrent_creation_with_shared_base() -> None:
    def setup():
        class Base:
            a: int = 1

            @field_validator('a')
            @classmethod
            def val_a_1(cls, v: int) -> int:
                return v

            @field_validator('a')
            @classmethod
            def val_a_2(cls, v: int) -> int:
                return v

            @field_validator('a')
            @classmethod
            def val_a_3(cls, v: int) -> int:
                return v

        return Base

    def target(Base, _):
        @pydantic.dataclasses.dataclass
        class Sub(Base):
            b: int

        assert Sub(b='1').b == 1

    run_concurrently(setup, target)


def test_model_rebuild_concurrent_subclass_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test targeted at our `LazyLocalNamespace.data` property implementation."""

    def setup():
        monkeypatch.delitem(globals(), 'Later', raising=False)

        class Model(BaseModel):
            # `Later` isn't defined yet, so the field is deferred and no annotations cache is set on the class:
            x: Later  # noqa: F821  # pyright: ignore[reportUndefinedVariable]

        # Widen the class dict so that iterating over it takes long enough for the race to happen:
        for i in range(3000):
            setattr(Model, f'attr_{i}', i)

        # Dynamically set the item in globals instead of a simple assignment to force `ForwardRef.evaluate()` into looking at the
        # provided namespace during evaluation (otherwise it doesn't look at globals/locals and uses `ForwardRef.__cell__` directly)
        monkeypatch.setitem(globals(), 'Later', int)
        return Model

    def target(Model, index: int):
        if index == 0:
            # Collecting the fields of the subclass reads the annotations of `Model` for the first time:
            class Sub(Model):
                pass

            assert Sub(x='1').x == 1
        else:
            Model.model_rebuild(force=True)

    run_concurrently(setup, target)


def test_model_force_rebuild_concurrent_instantiation() -> None:
    """Test targeted at our logic in `model_rebuild()`, when we set back mocks on already complete models."""

    def setup():
        class Model(BaseModel):
            x: int

        assert Model(x=1).x == 1  # `Model` is complete, with a real validator set on the class
        return Model

    def target(Model, index):
        if index == 0:
            Model.model_rebuild(force=True)
        else:
            assert Model(x='1').x == 1

    run_concurrently(setup, target)
