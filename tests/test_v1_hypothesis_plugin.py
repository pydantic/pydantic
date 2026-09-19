"""Regression tests for the Pydantic V1 Hypothesis plugin.

`pydantic/v1/_hypothesis_plugin.py` lives in the V1 namespace but ships with
Pydantic V2. It used to import `pydantic`, `pydantic.color` and
`pydantic.types` directly, which under V2 resolve to the V2 modules, so reading
V1-only names off them (`r_rgba`, `ConstrainedNumberMeta`, `_DEFINED_TYPES`)
raised `AttributeError` at import time.
"""

import pytest

from pydantic.v1 import StrictBool, conint


def test_v1_hypothesis_plugin_imports() -> None:
    """The plugin must import cleanly under Pydantic V2."""
    pytest.importorskip('hypothesis')

    import pydantic.v1._hypothesis_plugin as plugin

    assert plugin.__name__ == 'pydantic.v1._hypothesis_plugin'


def test_v1_hypothesis_plugin_registers_strategies() -> None:
    """The strategies the plugin registers must still resolve under Pydantic V2."""
    st = pytest.importorskip('hypothesis.strategies')
    given = pytest.importorskip('hypothesis').given
    settings = pytest.importorskip('hypothesis').settings

    pytest.importorskip('pydantic.v1._hypothesis_plugin')

    @settings(max_examples=5, deadline=None)
    @given(st.from_type(StrictBool))
    def check_bool(value: bool) -> None:
        assert isinstance(value, bool)

    check_bool()

    @settings(max_examples=5, deadline=None)
    @given(st.from_type(conint(gt=5)))
    def check_conint(value: int) -> None:
        assert isinstance(value, int)
        assert value > 5

    check_conint()
