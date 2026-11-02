# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..shared.reasoning_effort import ReasoningEffort

class Reasoning(BaseModel):
    """The reasoning configuration applied by this update."""
    effort: Optional[ReasoningEffort] = None

class ResponseConfigurationUpdateItem(BaseModel):
    """
    A configuration update that applies to subsequent responses until it is
    replaced by another configuration update.
    """
    id: str
    type: Literal['configuration_update']
    reasoning: Optional[Reasoning] = None
