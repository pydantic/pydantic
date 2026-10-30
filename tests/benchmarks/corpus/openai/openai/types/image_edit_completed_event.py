# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal
from .._models import BaseModel

class UsageInputTokensDetails(BaseModel):
    """The input tokens detailed information for the image generation."""
    image_tokens: int
    text_tokens: int

class Usage(BaseModel):
    """
    For the GPT image models only, the token usage information for the image generation.
    """
    input_tokens: int
    input_tokens_details: UsageInputTokensDetails
    output_tokens: int
    total_tokens: int

class ImageEditCompletedEvent(BaseModel):
    """Emitted when image editing has completed and the final image is available."""
    b64_json: str
    background: Literal['transparent', 'opaque', 'auto']
    created_at: int
    output_format: Literal['png', 'webp', 'jpeg']
    quality: Literal['low', 'medium', 'high', 'xhigh', 'max', 'auto']
    size: Union[str, Literal['1024x1024', '1024x1536', '1536x1024', 'auto']]
    type: Literal['image_edit.completed']
    usage: Usage
    safety_identifier: Optional[str] = None
