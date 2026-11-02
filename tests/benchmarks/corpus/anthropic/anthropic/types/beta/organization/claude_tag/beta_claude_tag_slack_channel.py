
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ....._models import BaseModel
from ..beta_claude_tag_settings import BetaClaudeTagSettings
from ..beta_claude_tag_setting_sources import BetaClaudeTagSettingSources
from ..beta_claude_tag_slack_channel_identifiers import BetaClaudeTagSlackChannelIdentifiers

class BetaClaudeTagSlackChannel(BaseModel):
    """
    A Slack channel set up for Claude Tag, with the settings it stores or, with `include_inherited`, the settings that apply in it.
    """
    id: str
    created_at: datetime
    settings: BetaClaudeTagSettings
    slack: BetaClaudeTagSlackChannelIdentifiers
    sources: BetaClaudeTagSettingSources
    type: Literal['slack_channel']
    updated_at: datetime
