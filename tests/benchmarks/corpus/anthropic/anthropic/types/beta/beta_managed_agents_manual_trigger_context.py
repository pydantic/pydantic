
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsManualTriggerContext(BaseModel):
    """
    The run was started manually by creating a session directly against the deployment.
    """
    type: Literal['manual']
