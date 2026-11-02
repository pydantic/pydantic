
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaMessageBatchRequestCounts(BaseModel):
    canceled: int
    errored: int
    expired: int
    processing: int
    succeeded: int
