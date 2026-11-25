
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaOutputBehaviorUpdateExisting(BaseModel):
    """Write the result into the input memory store instead of a new memory store.

    The credential must be allowed to write memory stores, or the request returns a 403 error. While another `update_existing` dream on the same memory store hasn't fully stopped, the request returns a 409 error.
    """
    memory_store_id: str
    type: Literal['update_existing']
