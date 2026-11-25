
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from ...._models import BaseModel
from ....types.beta import BetaToolUseBlock

class BetaToolsetCallContext(BaseModel):
    """What a member receives alongside its input: the `tool_use` block the call answers
    (`context.tool_use.id`). `None` only when a member is invoked outside any model call."""
    tool_use: BetaToolUseBlock | None = None
