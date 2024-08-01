from importlib import import_module
from typing import Any, Dict, Tuple


class CachedImportManager:
    def __init__(self) -> None:
        self._attr_cache: Dict[Tuple[str, str], Any] = {}
        self._module_cache: Dict[str, Any] = {}

    def get_cached_attr(self, attr_name: str, module_name: str) -> Any:
        if (key := (module_name, attr_name)) in self._attr_cache:
            return self._attr_cache[key]

        if module_name in self._module_cache:
            module = self._module_cache[module_name]
        else:
            module = import_module(module_name)
            self._module_cache[module_name] = module
        self._attr_cache[key] = getattr(module, attr_name)
        return self._attr_cache[key]


import_manager = CachedImportManager()
