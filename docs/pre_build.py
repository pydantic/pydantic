#!/usr/bin/env python3
import os
import re


def main():
    this_dir = os.path.dirname(__file__)
    real_history_file = os.path.join(this_dir, '../HISTORY.md')
    tmp_history_file = os.path.join(this_dir, 'changelog.md')

    with open(real_history_file) as f:
        history = f.read()

    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/pydantic/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    with open(tmp_history_file, 'w') as f:
        f.write(history)


if __name__ == '__main__':
    main()
