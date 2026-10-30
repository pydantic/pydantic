# Modified HTTPX2 2.16.0 support types; see HTTPX2-LICENSE.
from typing import Union
TimeoutTypes = Union[float | None, tuple[float | None, float | None, float | None, float | None], 'Timeout']
