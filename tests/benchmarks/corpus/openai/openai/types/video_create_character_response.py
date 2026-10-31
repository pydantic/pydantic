# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel

class VideoCreateCharacterResponse(BaseModel):
    id: Optional[str] = None
    created_at: int
    name: Optional[str] = None
