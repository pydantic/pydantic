
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_raw_content_block_delta import BetaRawContentBlockDelta

class BetaRawContentBlockDeltaEvent(BaseModel):
    delta: BetaRawContentBlockDelta
    index: int
    type: Literal['content_block_delta']
