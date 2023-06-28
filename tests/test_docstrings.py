import sys

import pytest

try:
    from pytest_examples import CodeExample, EvalExample, find_examples
except ImportError:
    # pytest_examples is not installed on emscripten
    CodeExample = EvalExample = None

    def find_examples(*_directories):
        return []


@pytest.mark.skipif(sys.platform not in {'linux', 'darwin'}, reason='Only on linux and macos')
@pytest.mark.parametrize('example', find_examples('python/pydantic_core/core_schema.py'), ids=str)
def test_docstrings(example: CodeExample, eval_example: EvalExample):
    eval_example.set_config(quotes='single')

    if eval_example.update_examples:
        eval_example.format(example)
        eval_example.run_print_update(example)
    else:
        eval_example.lint(example)
        eval_example.run_print_check(example)


@pytest.mark.skipif(sys.platform not in {'linux', 'darwin'}, reason='Only on linux and macos')
@pytest.mark.parametrize('example', find_examples('README.md'), ids=str)
def test_readme(example: CodeExample, eval_example: EvalExample):
    eval_example.set_config(line_length=100, quotes='single')
    if eval_example.update_examples:
        eval_example.format(example)
    else:
        eval_example.lint(example)
        eval_example.run(example)
