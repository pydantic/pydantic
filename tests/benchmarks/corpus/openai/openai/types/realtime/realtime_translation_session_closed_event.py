# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeTranslationSessionClosedEvent(BaseModel):
    """Returned when a realtime translation session is closed."""
    event_id: str
    type: Literal['session.closed']
