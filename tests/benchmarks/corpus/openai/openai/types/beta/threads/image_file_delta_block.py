# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .image_file_delta import ImageFileDelta

class ImageFileDeltaBlock(BaseModel):
    """
    References an image [File](https://developers.openai.com/api/reference/resources/files) in the content of a message.
    """
    index: int
    type: Literal['image_file']
    image_file: Optional[ImageFileDelta] = None
