
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from ...._models import BaseModel
from .beta_claude_tag_setting_source import BetaClaudeTagSettingSource

class BetaClaudeTagSettingSources(BaseModel):
    """For each setting, the settings level its value in `settings` comes from.

    Without `include_inherited`, a setting the channel or workspace stores has a source that names the channel or workspace itself, and one it does not store has null, or an empty list for `instructions`. With `include_inherited=true` no member is null: a value that no settings level sets has the source `default`.
    """
    enabled: Optional[BetaClaudeTagSettingSource] = None
    environment_id: Optional[BetaClaudeTagSettingSource] = None
    guest_policy: Optional[BetaClaudeTagSettingSource] = None
    instructions: List[BetaClaudeTagSettingSource]
    model: Optional[BetaClaudeTagSettingSource] = None
