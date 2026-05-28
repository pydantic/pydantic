"""Tests for the docs plugin code-upgrade logic (docs/plugins/main.py).

These tests verify that the Ruff-based ``_upgrade_code`` replacement
produces correct pyupgrade + unused-import-removal results via subprocess,
without needing the full MkDocs dependency chain.
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap

import pytest

RUFF_BIN = shutil.which('ruff')
pytestmark = pytest.mark.skipif(RUFF_BIN is None, reason='ruff not found on PATH')


def _upgrade_code(code: str, min_version: int) -> str:
    """Mirror of docs/plugins/main.py::_upgrade_code for isolated testing."""
    assert RUFF_BIN is not None
    result = subprocess.run(
        [
            RUFF_BIN,
            'check',
            '--select',
            'UP,F401',
            '--fix',
            '--target-version',
            f'py3{min_version}',
            '--isolated',
            '--stdin-filename',
            'example.py',
            '-',
        ],
        input=code,
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1), f'ruff exited with {result.returncode}: {result.stderr}'
    return result.stdout


class TestUpgradeCode:
    def test_optional_to_union(self):
        code = textwrap.dedent("""\
            from typing import Optional

            x: Optional[int] = None
        """)
        result = _upgrade_code(code, 10)
        assert 'Optional' not in result
        assert 'int | None' in result

    def test_list_to_builtin_py310(self):
        code = textwrap.dedent("""\
            from typing import List

            x: List[int] = []
        """)
        result = _upgrade_code(code, 10)
        assert 'list[int]' in result
        assert 'from typing import List' not in result

    def test_list_kept_for_py39(self):
        """Ruff treats List→list as unsafe for py39 runtime annotations, matching pyupgrade's keep_runtime_typing."""
        code = textwrap.dedent("""\
            from typing import List

            x: List[int] = []
        """)
        result = _upgrade_code(code, 9)
        assert 'List[int]' in result

    def test_unused_import_removed(self):
        code = textwrap.dedent("""\
            from typing import Optional, Dict

            x: int | None = None
        """)
        result = _upgrade_code(code, 10)
        assert 'import' not in result

    def test_no_change_for_modern_code(self):
        code = textwrap.dedent("""\
            x: int | None = None
        """)
        result = _upgrade_code(code, 10)
        assert result.strip() == code.strip()

    def test_target_version_respected(self):
        """Python 3.9 can use list[int] (PEP 585) but not X | None (PEP 604)."""
        code = textwrap.dedent("""\
            from typing import Optional

            x: Optional[int] = None
        """)
        result_39 = _upgrade_code(code, 9)
        assert 'Optional' in result_39, 'should keep Optional for 3.9 target'

        result_310 = _upgrade_code(code, 10)
        assert 'int | None' in result_310, 'should convert to union for 3.10 target'

    def test_multiple_typing_imports(self):
        code = textwrap.dedent("""\
            from typing import Dict, List, Optional, Set, Tuple

            def f(a: List[int], b: Dict[str, int], c: Optional[Set[Tuple[int, ...]]]) -> None:
                pass
        """)
        result = _upgrade_code(code, 10)
        assert 'list[int]' in result
        assert 'dict[str, int]' in result
        assert 'set[tuple[int, ...]] | None' in result

    def test_preserves_non_typing_code(self):
        code = textwrap.dedent("""\
            from pydantic import BaseModel

            class User(BaseModel):
                name: str
                age: int
        """)
        result = _upgrade_code(code, 10)
        assert result.strip() == code.strip()

    def test_isolated_from_project_config(self):
        """--isolated flag prevents project pyproject.toml from affecting results."""
        code = textwrap.dedent("""\
            x = 1
            print(x)
        """)
        result = _upgrade_code(code, 10)
        assert 'print(x)' in result
