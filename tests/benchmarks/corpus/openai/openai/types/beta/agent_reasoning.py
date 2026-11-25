# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class AgentReasoning(BaseModel):
    """The reasoning configuration used by an agent."""
    effort: Optional[Literal['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']] = None
    summary: Optional[Literal['concise', 'detailed', 'auto']] = None
