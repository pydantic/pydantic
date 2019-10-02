#!/usr/bin/env python3
import re
from pathlib import Path

THIS_DIR = Path(__file__).parent


def main():
    history = (THIS_DIR / '../HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/pydantic/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    (THIS_DIR / 'changelog.md').write_text(history)


if __name__ == '__main__':
    main()
