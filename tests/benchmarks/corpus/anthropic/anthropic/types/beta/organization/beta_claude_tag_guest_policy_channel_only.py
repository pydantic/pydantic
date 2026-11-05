
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaClaudeTagGuestPolicyChannelOnly(BaseModel):
    """Claude answers with only the Bundles attached to the channel itself."""
    type: Literal['channel_only']
