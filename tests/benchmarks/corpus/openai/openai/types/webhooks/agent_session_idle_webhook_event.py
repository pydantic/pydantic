# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Data(BaseModel):
    id: str
    environment_type: str
    environment_id: Optional[str] = None

class AgentSessionIdleWebhookEvent(BaseModel):
    """Sent when an agent session becomes idle."""
    id: str
    created_at: int
    data: Data
    object: Literal['event']
    type: Literal['agent.session.idle']
