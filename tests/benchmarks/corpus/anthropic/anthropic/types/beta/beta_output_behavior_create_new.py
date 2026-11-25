
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaOutputBehaviorCreateNew(BaseModel):
    """
    Write the result to a new memory store that starts as a copy of the input memory store. This is the default.

    The new memory store is in the same workspace as the dream. The dream doesn't change the input memory store.
    """
    type: Literal['create_new']
