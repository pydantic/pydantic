# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class Image(BaseModel):
    file_id: Optional[str] = None

class CodeInterpreterOutputImage(BaseModel):
    index: int
    type: Literal['image']
    image: Optional[Image] = None
