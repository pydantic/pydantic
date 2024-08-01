from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel

_type_cache = {}


def import_cached_base_model() -> type['BaseModel']:
    if 'BaseModel' in _type_cache:
        return _type_cache['BaseModel']
    else:
        from pydantic import BaseModel

        _type_cache['BaseModel'] = BaseModel
        return BaseModel
