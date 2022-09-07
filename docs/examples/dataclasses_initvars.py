from dataclasses import InitVar
from pathlib import Path
from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass
class PathData:
    path: Path
    base_path: InitVar[Optional[Path]]

    def __post_init__(self, base_path):
        print(f'Received path={self.path!r}, base_path={base_path!r}')

    def __post_init_post_parse__(self, base_path):
        if base_path is not None:
            self.path = base_path / self.path


path_data = PathData('world', base_path='/hello')
# Received path='world', base_path='/hello'
assert path_data.path == Path('/hello/world')
