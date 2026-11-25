
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaClaudeTagSlackChannelIdentifiers(BaseModel):
    """The identifiers Slack shows for a channel.

    They are Slack's own, not identifiers of this API.
    """
    channel_id: str
    workspace_id: str
