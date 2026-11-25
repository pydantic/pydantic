# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class VoiceConsent(BaseModel):
    """A consent recording used to authorize creation of a custom voice."""
    id: str
    created_at: int
    language: str
    name: str
    object: Literal['audio.voice_consent']
