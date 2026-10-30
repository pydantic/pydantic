
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel
from .beta_claude_tag_guest_policy import BetaClaudeTagGuestPolicy

class BetaClaudeTagSettings(BaseModel):
    """Claude Tag settings.

    Without `include_inherited`, a setting that is null is not set on the settings level and is inherited. With it, `enabled` and `guest_policy` are never null, and `instructions`, `model` and `environment_id` are null when no settings level sets them.
    """
    enabled: Optional[bool] = None
    environment_id: Optional[str] = None
    guest_policy: Optional[BetaClaudeTagGuestPolicy] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
