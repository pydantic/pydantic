# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from ..chatkit_workflow import ChatKitWorkflow
from .chat_session_status import ChatSessionStatus
from .chat_session_rate_limits import ChatSessionRateLimits
from .chat_session_chatkit_configuration import ChatSessionChatKitConfiguration

class ChatSession(BaseModel):
    """Represents a ChatKit session and its resolved configuration."""
    id: str
    chatkit_configuration: ChatSessionChatKitConfiguration
    client_secret: str
    expires_at: int
    max_requests_per_1_minute: int
    object: Literal['chatkit.session']
    rate_limits: ChatSessionRateLimits
    status: ChatSessionStatus
    user: str
    workflow: ChatKitWorkflow
