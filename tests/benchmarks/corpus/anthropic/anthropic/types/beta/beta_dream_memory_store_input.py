
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaDreamMemoryStoreInput(BaseModel):
    """The memory store that a dream reads, given as an entry in `inputs`.

    With `output_behavior` set to `update_existing`, the dream writes its result into this memory store. Otherwise the dream doesn't change it.
    """
    memory_store_id: str
    type: Literal['memory_store']
