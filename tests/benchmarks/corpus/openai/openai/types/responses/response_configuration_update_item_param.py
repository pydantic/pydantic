# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..shared.reasoning_effort import ReasoningEffort

class Reasoning(BaseModel):
    """Updates to reasoning configuration. Only effort is supported."""
    effort: Optional[ReasoningEffort] = None

class ResponseConfigurationUpdateItemParam(BaseModel):
    """An update to the conversation's response configuration.

    The configuration
    remains in effect for subsequent responses until it is replaced by another
    configuration update.
    """
    type: Literal['configuration_update']
    id: Optional[str] = None
    reasoning: Optional[Reasoning] = None
