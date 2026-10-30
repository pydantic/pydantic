# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .image_url import ImageURL
from ...._models import BaseModel

class ImageURLContentBlock(BaseModel):
    """References an image URL in the content of a message."""
    image_url: ImageURL
    type: Literal['image_url']
