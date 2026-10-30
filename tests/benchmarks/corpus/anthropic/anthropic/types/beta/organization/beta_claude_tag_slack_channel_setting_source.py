
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaClaudeTagSlackChannelSettingSource(BaseModel):
    """The value comes from the addressed Slack channel itself."""
    slack_channel_id: str
    type: Literal['slack_channel']
