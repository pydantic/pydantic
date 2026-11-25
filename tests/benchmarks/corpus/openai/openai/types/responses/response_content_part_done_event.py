# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .response_output_text import ResponseOutputText
from .response_output_refusal import ResponseOutputRefusal

class PartReasoningText(BaseModel):
    """Reasoning text from the model."""
    text: str
    type: Literal['reasoning_text']
Part: TypeAlias = Annotated[Union[ResponseOutputText, ResponseOutputRefusal, PartReasoningText], PropertyInfo(discriminator='type')]

class ResponseContentPartDoneEvent(BaseModel):
    """Emitted when a content part is done."""
    content_index: int
    item_id: str
    output_index: int
    part: Part
    sequence_number: int
    type: Literal['response.content_part.done']
