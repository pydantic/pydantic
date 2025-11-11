import sys
from pathlib import Path

import pytest

try:
    from pytest_examples import CodeExample, EvalExample, find_examples
except ImportError:
    # pytest_examples is not installed on emscripten
    CodeExample = EvalExample = None

    def find_examples(*_directories):
        return []


PYDANTIC_CORE_DIR = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(CodeExample is None or sys.platform not in {'linux', 'darwin'}, reason='Only on linux and macos')
@pytest.mark.parametrize(
    'example', find_examples(str(PYDANTIC_CORE_DIR / 'python/pydantic_core/core_schema.py')), ids=str
)
@pytest.mark.thread_unsafe  # TODO investigate why pytest_examples seems to be thread unsafe here
def test_docstrings(example: CodeExample, eval_example: EvalExample):
    eval_example.set_config(quotes='single')

    if eval_example.update_examples:
        eval_example.format(example)
        eval_example.run_print_update(example)
    else:
        eval_example.lint(example)
        eval_example.run_print_check(example)


@pytest.mark.skipif(CodeExample is None or sys.platform not in {'linux', 'darwin'}, reason='Only on linux and macos')
@pytest.mark.parametrize('example', find_examples(str(PYDANTIC_CORE_DIR / 'README.md')), ids=str)
@pytest.mark.thread_unsafe  # TODO investigate why pytest_examples seems to be thread unsafe here
def test_readme(example: CodeExample, eval_example: EvalExample):
    eval_example.set_config(line_length=100, quotes='single')
    if eval_example.update_examples:
        eval_example.format(example)
    else:
        eval_example.lint(example)
        eval_example.run(example)
