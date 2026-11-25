# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from .image import Image
from .._models import BaseModel

class UsageInputTokensDetails(BaseModel):
    """The input tokens detailed information for the image generation."""
    image_tokens: int
    text_tokens: int

class UsageOutputTokensDetails(BaseModel):
    """The output token details for the image generation."""
    image_tokens: int
    text_tokens: int

class Usage(BaseModel):
    """For `gpt-image-1` only, the token usage information for the image generation."""
    input_tokens: int
    input_tokens_details: UsageInputTokensDetails
    output_tokens: int
    total_tokens: int
    output_tokens_details: Optional[UsageOutputTokensDetails] = None

class ImagesResponse(BaseModel):
    """The response from the image generation endpoint."""
    created: int
    background: Optional[Literal['transparent', 'opaque']] = None
    data: Optional[List[Image]] = None
    output_format: Optional[Literal['png', 'webp', 'jpeg']] = None
    quality: Optional[Literal['low', 'medium', 'high', 'xhigh', 'max']] = None
    safety_identifier: Optional[str] = None
    size: Union[str, Literal['1024x1024', '1024x1536', '1536x1024'], None] = None
    usage: Optional[Usage] = None
