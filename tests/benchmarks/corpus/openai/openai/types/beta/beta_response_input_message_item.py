# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_input_message_content_list import BetaResponseInputMessageContentList

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseInputMessageItem(BaseModel):
    id: str
    content: BetaResponseInputMessageContentList
    role: Literal['user', 'system', 'developer']
    type: Literal['message']
    agent: Optional[Agent] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
