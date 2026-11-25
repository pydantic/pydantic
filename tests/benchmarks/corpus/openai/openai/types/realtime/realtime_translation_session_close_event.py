# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeTranslationSessionCloseEvent(BaseModel):
    """Gracefully close the realtime translation session.

    The server flushes pending
    input audio and emits any remaining translated output before closing the
    session.
    """
    type: Literal['session.close']
    event_id: Optional[str] = None
