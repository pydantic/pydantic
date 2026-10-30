# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class RealtimeResponseUsageOutputTokenDetails(BaseModel):
    """Details about the output tokens used in the Response."""
    audio_tokens: Optional[int] = None
    text_tokens: Optional[int] = None
