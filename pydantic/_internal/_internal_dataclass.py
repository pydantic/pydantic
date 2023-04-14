import sys
from dataclasses import dataclass as stdlib_dataclass
from typing import TYPE_CHECKING, Any, Dict

dataclass_kwargs: Dict[str, Any]
if sys.version_info >= (3, 10):
    dataclass_kwargs = {'slots': True}
else:
    dataclass_kwargs = {}

if TYPE_CHECKING:
    slots_dataclass = stdlib_dataclass
else:

    def slots_dataclass(*args: Any, **kwargs: Any) -> Any:
        kwargs = {**dataclass_kwargs, **kwargs}
        return stdlib_dataclass(*args, **kwargs)
