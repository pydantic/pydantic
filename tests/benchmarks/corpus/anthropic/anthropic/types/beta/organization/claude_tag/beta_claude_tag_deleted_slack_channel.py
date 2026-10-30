
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class BetaClaudeTagDeletedSlackChannel(BaseModel):
    """Confirms that a Slack channel was removed from Claude Tag."""
    id: str
    type: Literal['slack_channel_deleted']
