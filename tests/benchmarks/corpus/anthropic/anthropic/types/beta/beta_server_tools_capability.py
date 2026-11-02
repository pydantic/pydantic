
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel
from .beta_capability_support import BetaCapabilitySupport

class BetaServerToolsCapability(BaseModel):
    """Web search and code execution tool support, with one entry per tool."""
    code_execution: BetaCapabilitySupport
    supported: bool
    web_search: BetaCapabilitySupport
