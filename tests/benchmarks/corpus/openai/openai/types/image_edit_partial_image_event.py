# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal
from .._models import BaseModel

class ImageEditPartialImageEvent(BaseModel):
    """Emitted when a partial image is available during image editing streaming."""
    b64_json: str
    background: Literal['transparent', 'opaque', 'auto']
    created_at: int
    output_format: Literal['png', 'webp', 'jpeg']
    partial_image_index: int
    quality: Literal['low', 'medium', 'high', 'xhigh', 'max', 'auto']
    size: Union[str, Literal['1024x1024', '1024x1536', '1536x1024', 'auto']]
    type: Literal['image_edit.partial_image']
