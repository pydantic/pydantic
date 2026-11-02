
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionRetriesExhausted(BaseModel):
    """
    The turn ended because repeated errors exhausted the retry budget or an error escalated to `retry_status: 'exhausted'`.
    """
    type: Literal['retries_exhausted']
