
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsEffortXhigh(BaseModel):
    """Extra-high effort. Not all models accept this level."""
    type: Literal['xhigh']
