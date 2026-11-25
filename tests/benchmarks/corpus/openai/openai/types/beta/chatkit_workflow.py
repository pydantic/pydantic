# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from ..._models import BaseModel

class Tracing(BaseModel):
    """Tracing settings applied to the workflow."""
    enabled: bool

class ChatKitWorkflow(BaseModel):
    """Workflow metadata and state returned for the session."""
    id: str
    state_variables: Optional[Dict[str, Union[str, bool, float]]] = None
    tracing: Tracing
    version: Optional[str] = None
