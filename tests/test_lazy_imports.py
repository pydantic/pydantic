import importlib
import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest

from pydantic import PydanticUndefinedAnnotation, PydanticUserError

pytestmark = pytest.mark.skipif(sys.version_info < (3, 15), reason='Requires lazy imports introduced in Python 3.15')


@pytest.fixture
def import_lazy_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator:
    """Write modules with the provided names to disk, and import the first one."""
    created: list[str] = []

    def run(**sources: str):
        for name, source in sources.items():
            (tmp_path / f'{name}.py').write_text(textwrap.dedent(source))
            created.append(name)
        importlib.invalidate_caches()
        monkeypatch.syspath_prepend(str(tmp_path))
        return importlib.import_module(created[0])

    yield run

    for name in created:
        sys.modules.pop(name, None)


def test_lazy_import_in_annotation(create_module) -> None:
    module = create_module(
        textwrap.dedent("""
        lazy from datetime import date

        from pydantic import BaseModel

        class Model(BaseModel):
            d: date
        """)
    )

    assert module.Model.__pydantic_complete__
    assert module.Model(d='2026-01-01').d == module.date(2026, 1, 1)


def test_lazy_import_circular_models(import_lazy_modules) -> None:
    mod_a = import_lazy_modules(
        lazy_cycle_a="""
        lazy from lazy_cycle_b import B

        from pydantic import BaseModel

        class A(BaseModel):
            b: B | None
        """,
        lazy_cycle_b="""
        lazy from lazy_cycle_a import A

        from pydantic import BaseModel

        class B(BaseModel):
            a: A | None
        """,
    )
    mod_b = sys.modules['lazy_cycle_b']

    # Creating `A` triggered the lazy import of `lazy_cycle_b`. When creating `B`, `A` isn't defined
    # yet (as `lazy_cycle_a` is partially initialized), so `B` is left incomplete and `lazy_cycle_b`
    # completes normally. Back in `lazy_cycle_a`, `B` is now available so `A` is complete:
    assert mod_a.A.__pydantic_complete__
    assert not mod_b.B.__pydantic_complete__

    # `B` is rebuilt automatically on first use:
    b = mod_b.B(a={'b': None})
    assert mod_b.B.__pydantic_complete__
    assert isinstance(b.a, mod_a.A)
    assert mod_b.B.model_fields['a'].annotation == mod_a.A | None

    a = mod_a.A(b={'a': None})
    assert isinstance(a.b, mod_b.B)


def test_lazy_import_circular_dataclasses(import_lazy_modules) -> None:
    mod_a = import_lazy_modules(
        lazy_dc_cycle_a="""
        lazy from lazy_dc_cycle_b import B

        from pydantic.dataclasses import dataclass

        @dataclass
        class A:
            b: B | None
        """,
        lazy_dc_cycle_b="""
        lazy from lazy_dc_cycle_a import A

        from pydantic.dataclasses import dataclass

        @dataclass
        class B:
            a: A | None
        """,
    )
    mod_b = sys.modules['lazy_dc_cycle_b']

    assert mod_a.A.__pydantic_complete__
    assert not mod_b.B.__pydantic_complete__

    b = mod_b.B(a={'b': None})
    assert mod_b.B.__pydantic_complete__
    assert isinstance(b.a, mod_a.A)


@pytest.mark.xfail(
    reason='Waiting for https://github.com/python/cpython/pull/156940 to be released in the final 3.15 release.'
)
def test_lazy_import_missing_module(create_module) -> None:
    module = create_module(
        textwrap.dedent("""
        lazy from does_not_exist import Missing

        from pydantic import BaseModel

        class Model(BaseModel):
            x: Missing
        """)
    )

    assert not module.Model.__pydantic_complete__

    with pytest.raises(
        PydanticUndefinedAnnotation,
        match="Unable to resolve the import of 'does_not_exist': No module named 'does_not_exist'",
    ) as exc_info:
        module.Model.model_rebuild()

    assert exc_info.value.name == 'does_not_exist'
    name_error = exc_info.value.__cause__
    assert isinstance(name_error, NameError)
    assert isinstance(name_error.__cause__, ModuleNotFoundError)

    with pytest.raises(PydanticUserError, match='`Model` is not fully defined'):
        module.Model(x=1)


@pytest.mark.xfail(
    reason='Waiting for https://github.com/python/cpython/pull/156940 to be released in the final 3.15 release.'
)
def test_lazy_import_missing_name(create_module) -> None:
    module = create_module(
        textwrap.dedent("""
        lazy from math import does_not_exist

        from pydantic import BaseModel

        class Model(BaseModel):
            x: does_not_exist
        """)
    )

    assert not module.Model.__pydantic_complete__

    with pytest.raises(
        PydanticUndefinedAnnotation,
        match="Unable to resolve the import of 'does_not_exist': cannot import name 'does_not_exist' from 'math'",
    ) as exc_info:
        module.Model.model_rebuild()

    assert exc_info.value.name == 'does_not_exist'
    name_error = exc_info.value.__cause__
    assert isinstance(name_error, NameError)
    assert isinstance(name_error.__cause__, ImportError)
