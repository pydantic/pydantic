# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Any
from typing_extensions import TypeVar
LifespanContextT = TypeVar('LifespanContextT', default=dict[str, Any])
RequestT = TypeVar('RequestT', default=Any)
