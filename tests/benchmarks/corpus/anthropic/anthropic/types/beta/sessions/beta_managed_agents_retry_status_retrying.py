
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsRetryStatusRetrying(BaseModel):
    """The server is retrying automatically.

    Client should wait; the same error type may fire again as retrying, then once as exhausted when the retry budget runs out.
    """
    type: Literal['retrying']
