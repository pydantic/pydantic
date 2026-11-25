# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class ChatSessionHistory(BaseModel):
    """History retention preferences returned for the session."""
    enabled: bool
    recent_threads: Optional[int] = None
