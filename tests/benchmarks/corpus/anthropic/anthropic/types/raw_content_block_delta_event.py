
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .raw_content_block_delta import RawContentBlockDelta

class RawContentBlockDeltaEvent(BaseModel):
    delta: RawContentBlockDelta
    index: int
    type: Literal['content_block_delta']
