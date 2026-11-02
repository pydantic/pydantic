# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from .._models import BaseModel
from .moderation import Moderation

class ModerationCreateResponse(BaseModel):
    """Represents if a given text input is potentially harmful."""
    id: str
    model: str
    results: List[Moderation]
