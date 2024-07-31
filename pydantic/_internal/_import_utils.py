from importlib import import_module
from typing import Any

_cache = {}


def get_cached_component(module_name: str, component_name: str) -> Any:
    if key := (module_name, component_name) not in _cache:
        module = import_module(module_name)
        _cache[key] = getattr(module, component_name)
    return _cache[key]
