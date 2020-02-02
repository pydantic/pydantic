from pathlib import Path
from typing import Pattern, Optional

from pydantic import validate_arguments, DirectoryPath

@validate_arguments
def find_file(path: DirectoryPath, regex: Pattern) -> Optional[Path]:
    for f in path.glob('**/*'):
        if f.is_file() and regex.fullmatch(str(f.relative_to(path))):
            return f

print(find_file('/etc/', '^sys.*'))
