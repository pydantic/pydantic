
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel
from .capability_support import CapabilitySupport

class ServerToolsCapability(BaseModel):
    """Web search and code execution tool support, with one entry per tool."""
    code_execution: CapabilitySupport
    supported: bool
    web_search: CapabilitySupport
