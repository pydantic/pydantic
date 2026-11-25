
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_claude_tag_slack_channel_identifiers import BetaClaudeTagSlackChannelIdentifiers

class BetaClaudeTagSlackGridChannelSettingSource(BaseModel):
    """
    The value comes from the addressed channel as it is set up under another workspace of its Enterprise Grid: a channel shared across the Grid keeps one Slack channel identifier in every workspace that sees it.
    """
    slack: BetaClaudeTagSlackChannelIdentifiers
    type: Literal['slack_grid_channel']
