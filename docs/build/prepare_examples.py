#!/usr/bin/env python3
import importlib
import inspect
import re
import sys
from pathlib import Path
from typing import Callable, List
from unittest.mock import patch


class MockPrint:
    def __init__(self, file: Path):
        self.file = file

    def __call__(self, *args):
        frame = inspect.currentframe().f_back.f_back.f_back
        if not self.file.samefile(frame.f_code.co_filename):
            raise RuntimeError("what's wrong here?")
        expected_comment: List[str] = []
        single_line: bool = False
        multi_line: bool = False
        target_line = frame.f_lineno
        sys.stdout.write(f'{target_line}\n')
        sys.stdout.write(' '.join(map(str, args)) + '\n')
        # for line in self.file.read_text().splitlines()[target_line:]:
        #     if re.match(SINGLE_LINE_COMMENT, line):
        #         if not single_line:
        #             single_line = True
        #         expected_comment.append(re.sub(STRIP_PATTERN, '', line))
        #     elif single_line:
        #         break
        #     elif re.match(MULTILINE_COMMENT, line):
        #         if multi_line:
        #             break
        #         multi_line = True
        #     else:
        #         if multi_line:
        #             expected_comment.append(re.sub(STRIP_PATTERN, '', line))
        #         else:
        #             break
        # if not single_line and not multi_line:
        #     raise Exception(f'NotFound expected comment. target_line is {target_line + 1}')
        # actual = str(args[0]).splitlines()
        # try:
        #     assert actual == expected_comment
        # except AssertionError:
        #     raise InvalidComment(self.file, actual, expected_comment)


THIS_DIR = Path(__file__).parent
EXAMPLES_ROOT = THIS_DIR / '..' / 'examples'


def main():
    sys.path.append(str(EXAMPLES_ROOT))
    for file in sorted(EXAMPLES_ROOT.glob('*.py')):
        if file.name == 'settings.py':
            # TODO
            continue
        if file.name == 'example2.py':
            continue
        print(file.name)
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = MockPrint(file)
            importlib.import_module(file.stem)
        break  # while testing


if __name__ == '__main__':
    main()
