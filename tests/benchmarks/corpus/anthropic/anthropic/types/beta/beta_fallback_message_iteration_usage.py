
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..model import Model
from ..._models import BaseModel
from .beta_cache_creation import BetaCacheCreation

class BetaFallbackMessageIterationUsage(BaseModel):
    """Token usage for the fallback-model attempt of a server-side fallback request.

    The terminal entry of a fallback-served turn: when a fallback hop's
    output is the returned message, the entry for the iteration that
    completed it carries this type in place of `message`. A declined hop
    and the serving hop's earlier tool-loop iterations produce `message`
    entries. Whether a fallback model served the response is signalled by
    the presence of this entry in `usage.iterations`.
    """
    cache_creation: Optional[BetaCacheCreation] = None
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    input_tokens: int
    model: Model
    output_tokens: int
    type: Literal['fallback_message']
