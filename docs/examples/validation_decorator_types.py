from pathlib import Path
from typing import Pattern, Optional

from pydantic import validate_arguments, DirectoryPath


@validate_arguments
def find_file(path: DirectoryPath, regex: Pattern, max=None) -> Optional[Path]:
    for i, f in enumerate(path.glob('**/*')):
        if max and i > max:
            return
        if f.is_file() and regex.fullmatch(str(f.relative_to(path))):
            return f


print(find_file('/etc/', '^sys.*'))
print(find_file('/etc/', '^foobar.*', max=3))
