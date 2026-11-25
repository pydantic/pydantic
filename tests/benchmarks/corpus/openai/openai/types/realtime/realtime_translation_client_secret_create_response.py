# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel
from .realtime_translation_session import RealtimeTranslationSession

class RealtimeTranslationClientSecretCreateResponse(BaseModel):
    """
    Response from creating a translation session and client secret for the Realtime API.
    """
    expires_at: int
    session: RealtimeTranslationSession
    value: str
