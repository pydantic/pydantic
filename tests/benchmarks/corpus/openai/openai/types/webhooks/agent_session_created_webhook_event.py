# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class DataConnect(BaseModel):
    remote_url: str

class Data(BaseModel):
    id: str
    environment_type: str
    connect: Optional[DataConnect] = None
    environment_id: Optional[str] = None

class AgentSessionCreatedWebhookEvent(BaseModel):
    """Sent when an agent session is created."""
    id: str
    created_at: int
    data: Data
    object: Literal['event']
    type: Literal['agent.session.created']
