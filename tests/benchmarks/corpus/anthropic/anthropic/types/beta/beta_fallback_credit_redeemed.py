
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaFallbackCreditRedeemed(BaseModel):
    """
    The reprice was applied: the retry is billed as if the conversation
    had been on the retry model all along.
    """
    type: Literal['redeemed']
