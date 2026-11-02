# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseImageGenCallPartialImageEvent(BaseModel):
    """Emitted when a partial image is available during image generation streaming."""
    item_id: str
    output_index: int
    partial_image_b64: str
    partial_image_index: int
    sequence_number: int
    type: Literal['response.image_generation_call.partial_image']
    background: Optional[str] = None
    output_format: Optional[str] = None
    quality: Optional[str] = None
    size: Optional[str] = None
