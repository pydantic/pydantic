import inspect
import re
import sys
from io import StringIO
from tempfile import NamedTemporaryFile
from typing import Any, TextIO

import pytest

import pydantic_core

DOCSTRING_REGEX = r'```py(.*?)```'


class DocstringTest:
    def method_a(self):
        """
        ```py
        assert 1 == 1
        assert 1 != 2
        ```

        ```py
        assert 1 != 3
        assert 2 + 2 == 4
        ```
        """
        pass

    def method_b(self):
        """
        ```py
        print('hello')
        print('world')
        ```
        """
        pass


class DocstringTestBadIndent:
    def method_a(self):
        """
          ```py
          assert 1 == 1
        print('badly indented line')
          ```
        """
        pass


def write_docstrings_to_test_file(obj_with_docstrings: Any, f: TextIO):
    for name, obj in inspect.getmembers(obj_with_docstrings):
        if obj.__doc__ is not None:
            for i, match in enumerate(re.finditer(DOCSTRING_REGEX, obj.__doc__, re.DOTALL)):
                code = match.group(1)
                f.write(f'def test_{name}_{i}():\n')
                lines = [line for line in code.splitlines() if line.strip()]
                initial_indent = len(lines[0]) - len(lines[0].lstrip())
                for line in lines:
                    if line[:initial_indent].strip():
                        raise ValueError(f'Unexpected indentation: {line}')
                    f.write(f'    {line[initial_indent:]}\n')
                f.write('\n')
    f.flush()


def test_write_docstrings_to_test_file():
    with StringIO('') as f:
        write_docstrings_to_test_file(DocstringTest, f)
        assert (
            f.getvalue()
            == """def test_method_a_0():
    assert 1 == 1
    assert 1 != 2

def test_method_a_1():
    assert 1 != 3
    assert 2 + 2 == 4

def test_method_b_0():
    print('hello')
    print('world')

"""
        )


def test_write_docstrings_to_test_file_raises_value_error():
    with StringIO('') as f, pytest.raises(ValueError):
        write_docstrings_to_test_file(DocstringTestBadIndent, f)


@pytest.mark.skipif(sys.platform == 'win32', reason='Windows does not support NamedTemporaryFile')
def test_docstrings():
    with NamedTemporaryFile('w', suffix='.py') as f:
        write_docstrings_to_test_file(pydantic_core.core_schema, f)
        exit_code = pytest.main([f.name])
        if exit_code != 0:
            sys.exit(exit_code)
