# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .image_url_delta import ImageURLDelta

class ImageURLDeltaBlock(BaseModel):
    """References an image URL in the content of a message."""
    index: int
    type: Literal['image_url']
    image_url: Optional[ImageURLDelta] = None
