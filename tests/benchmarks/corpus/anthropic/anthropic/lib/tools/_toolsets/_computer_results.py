
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from ._runnable import BetaToolsetCallContext
from ...._models import BaseModel
from ._computer_inputs import BetaComputerMemberName, BetaComputerMemberInput

class BetaComputerCursorPositionResult(BaseModel):
    """Where the cursor is, in screenshot pixels; rendered as `X={x},Y={y}`."""
    x: int
    y: int

class BetaComputerConfirmContext(BetaToolsetCallContext):
    """What the `confirm` callable is told about the call awaiting approval: the member and its parsed input, and
    the `tool_use` block being answered."""
    member: BetaComputerMemberName
    input: BetaComputerMemberInput
