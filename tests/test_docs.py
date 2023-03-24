from __future__ import annotations as _annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

index_main = None


class GroupModuleGlobals:
    def __init__(self) -> None:
        self.name = None
        self.module_dict: dict[str, str] = {}

    def get(self, name: str | None):
        if name is not None and name == self.name:
            return self.module_dict

    def set(self, name: str | None, module_dict: dict[str, str]):
        self.name = name
        if self.name is None:
            self.module_dict = None
        else:
            self.module_dict = module_dict


group_globals = GroupModuleGlobals()


class MockedDatetime(datetime):
    @staticmethod
    def now():
        return datetime(2032, 1, 2, 3, 4, 5, 6)


@pytest.mark.skipif(sys.platform not in {'linux', 'darwin'}, reason='Only bother on linux and macos')
@pytest.mark.parametrize('example', find_examples('docs'), ids=str)
def test_docs_examples(example: CodeExample, eval_example: EvalExample, tmp_path: Path, mocker):
    global index_main
    if example.path.name == 'index.md':
        if index_main is None:
            index_main = example.source
        else:
            (tmp_path / 'index_main.py').write_text(index_main)
            sys.path.append(str(tmp_path))

    prefix_settings = example.prefix_settings()
    test_settings = prefix_settings.get('test')
    lint_settings = prefix_settings.get('lint')
    if test_settings == 'skip' and lint_settings == 'skip':
        pytest.skip('both test and lint skipped')

    if test_settings == 'requires-3.10' and sys.version_info < (3, 10):
        pytest.skip('requires python 3.10')
    elif test_settings == 'requires-3.8' and sys.version_info < (3, 8):
        pytest.skip('requires python 3.8')

    group_name = prefix_settings.get('group')

    if '# ignore-above' in example.source:
        eval_example.set_config(ruff_ignore=['E402'])
    if group_name:
        eval_example.set_config(ruff_ignore=['F821'])

    if lint_settings != 'skip':
        if eval_example.update_examples:
            eval_example.format(example)
        else:
            eval_example.lint(example)

    if test_settings == 'skip':
        return
    elif test_settings and test_settings.startswith('xfail'):
        pytest.xfail(test_settings[5:])

    group_name = prefix_settings.get('group')
    d = group_globals.get(group_name)

    mocker.patch('datetime.datetime', MockedDatetime)
    mocker.patch('random.randint', return_value=3)

    if test_settings == 'no-print-intercept':
        d2 = eval_example.run(example, module_globals=d)
    elif eval_example.update_examples:
        d2 = eval_example.run_print_update(example, module_globals=d)
    else:
        d2 = eval_example.run_print_check(example, module_globals=d)

    group_globals.set(group_name, d2)
