# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Error(BaseModel):
    """The error reported while preparing the environment, if any."""
    code: str
    message: str
    type: str

class AgentSessionEnvironmentState(BaseModel):
    """The current state of a session environment."""
    id: str
    error: Optional[Error] = None
    status: Literal['pending', 'ready', 'connected', 'disconnected', 'suspended', 'expired', 'failed']
    type: str
