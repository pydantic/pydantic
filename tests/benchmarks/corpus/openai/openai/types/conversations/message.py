# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .text_content import TextContent
from .summary_text_content import SummaryTextContent
from .computer_screenshot_content import ComputerScreenshotContent
from ..responses.response_input_file import ResponseInputFile
from ..responses.response_input_text import ResponseInputText
from ..responses.response_input_image import ResponseInputImage
from ..responses.response_output_text import ResponseOutputText
from ..responses.response_output_refusal import ResponseOutputRefusal

class ContentReasoningText(BaseModel):
    """Reasoning text from the model."""
    text: str
    type: Literal['reasoning_text']
Content: TypeAlias = Annotated[Union[ResponseInputText, ResponseOutputText, TextContent, SummaryTextContent, ContentReasoningText, ResponseOutputRefusal, ResponseInputImage, ComputerScreenshotContent, ResponseInputFile], PropertyInfo(discriminator='type')]

class Message(BaseModel):
    """A message to or from the model."""
    id: str
    content: List[Content]
    role: Literal['unknown', 'user', 'assistant', 'system', 'critic', 'discriminator', 'developer', 'tool']
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['message']
    phase: Optional[Literal['commentary', 'final_answer']] = None
