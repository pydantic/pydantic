from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel


@lru_cache(maxsize=None)
def import_cached_base_model() -> type['BaseModel']:
    from pydantic import BaseModel

    return BaseModel
