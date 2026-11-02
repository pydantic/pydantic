# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class DataRequiredAction(BaseModel):
    """The action type. Retrieve the session for action details."""
    type: Literal['computer_use_approval_request', 'function_call', 'environment_connection']

class Data(BaseModel):
    id: str
    required_action: DataRequiredAction

class AgentSessionActionRequiredWebhookEvent(BaseModel):
    """Sent when an agent session requires an action.

    Retrieve the session for action details.
    """
    id: str
    created_at: int
    data: Data
    object: Literal['event']
    type: Literal['agent.session.action_required']
