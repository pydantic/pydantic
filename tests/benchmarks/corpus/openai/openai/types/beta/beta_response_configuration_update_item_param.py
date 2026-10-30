# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class Reasoning(BaseModel):
    """Updates to reasoning configuration. Only effort is supported."""
    effort: Optional[Literal['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']] = None

class BetaResponseConfigurationUpdateItemParam(BaseModel):
    """An update to the conversation's response configuration.

    The configuration
    remains in effect for subsequent responses until it is replaced by another
    configuration update.
    """
    type: Literal['configuration_update']
    id: Optional[str] = None
    agent: Optional[Agent] = None
    reasoning: Optional[Reasoning] = None
