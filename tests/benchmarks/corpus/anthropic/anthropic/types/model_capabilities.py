
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel
from .effort_capability import EffortCapability
from .capability_support import CapabilitySupport
from .thinking_capability import ThinkingCapability
from .server_tools_capability import ServerToolsCapability
from .context_management_capability import ContextManagementCapability

class ModelCapabilities(BaseModel):
    """Model capability information."""
    batch: CapabilitySupport
    citations: CapabilitySupport
    code_execution: CapabilitySupport
    context_management: ContextManagementCapability
    effort: EffortCapability
    image_input: CapabilitySupport
    pdf_input: CapabilitySupport
    server_tools: ServerToolsCapability
    structured_outputs: CapabilitySupport
    thinking: ThinkingCapability
