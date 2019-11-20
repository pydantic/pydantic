import re
from pathlib import Path
from typing import Dict


class EnvFileError(ValueError):
    pass


def read_env_file(file_path: Path, case_sensitive: bool = False) -> Dict[str, str]:
    file_vars: Dict[str, str] = {}
    for n, line in enumerate(re.split('[\r\n]+', file_path.read_text()), start=1):
        line = line.strip()
        if line and not line.startswith('#'):
            if re.match(r'\s*(\w+)\s*=\s*(.+?)\s*', line):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('\'"')
                file_vars[key if case_sensitive else key.lower()] = value
            else:
                raise EnvFileError(f'invalid assignment in {file_path} on line {n}\n  {line}')

    return file_vars
