# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class DecisionQuestionInputImage(BaseModel):
    """An image provided as a base64 data URL or a publicly accessible HTTP(S) URL.

    File IDs are not supported.
    """
    image_url: str
    type: Literal['input_image']
    detail: Optional[Literal['low', 'high', 'auto', 'original']] = None
