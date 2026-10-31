# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Voice(BaseModel):
    """A custom voice that can be used for audio output.

    Voices created from text prompts are supported only in Live.
    """
    id: str
    created_at: int
    name: str
    object: Literal['audio.voice']
    type: Literal['audio_sample', 'prompt']
    prompt: Optional[str] = None
