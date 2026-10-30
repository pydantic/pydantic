# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class Data(BaseModel):
    """Identifies the environment whose lifecycle changed."""
    id: str

class AgentEnvironmentFailedWebhookEvent(BaseModel):
    """
    Sent when setup fails for a prewarmed OpenAI-hosted environment before it is attached to a session.
    """
    id: str
    created_at: int
    data: Data
    object: Literal['event']
    type: Literal['agent.environment.failed']
