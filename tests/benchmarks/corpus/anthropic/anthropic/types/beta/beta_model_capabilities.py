
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_effort_capability import BetaEffortCapability
from .beta_capability_support import BetaCapabilitySupport
from .beta_thinking_capability import BetaThinkingCapability
from .beta_compaction_capability import BetaCompactionCapability
from .beta_server_tools_capability import BetaServerToolsCapability
from .beta_context_management_capability import BetaContextManagementCapability

class BetaModelCapabilities(BaseModel):
    """Model capability information."""
    batch: BetaCapabilitySupport
    citations: BetaCapabilitySupport
    code_execution: BetaCapabilitySupport
    compaction: Optional[BetaCompactionCapability] = None
    context_management: BetaContextManagementCapability
    effort: BetaEffortCapability
    image_input: BetaCapabilitySupport
    pdf_input: BetaCapabilitySupport
    server_tools: BetaServerToolsCapability
    structured_outputs: BetaCapabilitySupport
    thinking: BetaThinkingCapability
