
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionRefusal(BaseModel):
    """
    The turn ended because the model's response was refused, for example by a safety classifier.
    """
    type: Literal['refusal']
