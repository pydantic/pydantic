# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_response_output_text import BetaResponseOutputText
from .beta_response_output_refusal import BetaResponseOutputRefusal

class PartReasoningText(BaseModel):
    """Reasoning text from the model."""
    text: str
    type: Literal['reasoning_text']
Part: TypeAlias = Annotated[Union[BetaResponseOutputText, BetaResponseOutputRefusal, PartReasoningText], PropertyInfo(discriminator='type')]

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseContentPartAddedEvent(BaseModel):
    """Emitted when a new content part is added."""
    content_index: int
    item_id: str
    output_index: int
    part: Part
    sequence_number: int
    type: Literal['response.content_part.added']
    agent: Optional[Agent] = None
