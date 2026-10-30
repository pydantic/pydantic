# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_response_output_text import BetaResponseOutputText
from .beta_response_output_refusal import BetaResponseOutputRefusal
Content: TypeAlias = Annotated[Union[BetaResponseOutputText, BetaResponseOutputRefusal], PropertyInfo(discriminator='type')]

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseOutputMessage(BaseModel):
    """An output message from the model."""
    id: str
    content: List[Content]
    role: Literal['assistant']
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['message']
    agent: Optional[Agent] = None
    phase: Optional[Literal['commentary', 'final_answer']] = None
