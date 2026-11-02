
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaDreamModelConfig(BaseModel):
    """The model that runs a dream, from the request that created it.

    The dream uses this model for all of its work. The response always gives the model as an object, even if the request gave only a model ID.
    """
    id: str
    speed: Optional[Literal['standard', 'fast']] = None
