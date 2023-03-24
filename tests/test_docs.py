import sys
from pathlib import Path

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

index_main = None


@pytest.mark.parametrize('example', find_examples('docs'), ids=str)
def test_readme(example: CodeExample, eval_example: EvalExample, tmp_path: Path):
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

    if eval_example.update_examples:
        eval_example.format(example)
    else:
        eval_example.lint(example)

    if test_settings == 'skip':
        pass
    if test_settings == 'no-print-intercept':
        eval_example.run(example)
    elif eval_example.update_examples:
        eval_example.run_print_update(example)
    else:
        eval_example.run_print_check(example)
