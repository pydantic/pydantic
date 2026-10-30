# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .response_output_text import ResponseOutputText
from .response_output_refusal import ResponseOutputRefusal
Content: TypeAlias = Annotated[Union[ResponseOutputText, ResponseOutputRefusal], PropertyInfo(discriminator='type')]

class ResponseOutputMessage(BaseModel):
    """An output message from the model."""
    id: str
    content: List[Content]
    role: Literal['assistant']
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['message']
    phase: Optional[Literal['commentary', 'final_answer']] = None
