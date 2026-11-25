
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ..._models import BaseModel
from .beta_fallback_info import BetaFallbackInfo
from .beta_fallback_refusal_trigger import BetaFallbackRefusalTrigger

class BetaFallbackBlock(BaseModel):
    """Marks the point in `content` where one model's output gives way to the next.

    One block appears per hop where a preceding model actually ran this turn and
    declined. A turn where no preceding model ran and declined has no such
    boundary and carries no block — the signal for whether a fallback model
    served the response is the presence of a `fallback_message` entry in
    `usage.iterations`, not this block.

    The block is treated like a server-tool content block for streaming: it
    arrives via the standard `content_block_start` / `content_block_stop`
    pair and carries no deltas.
    """
    from_: BetaFallbackInfo = FieldInfo(alias='from')
    to: BetaFallbackInfo
    trigger: BetaFallbackRefusalTrigger
    type: Literal['fallback']
