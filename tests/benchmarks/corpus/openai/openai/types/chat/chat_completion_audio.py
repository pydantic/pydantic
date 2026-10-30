# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel

class ChatCompletionAudio(BaseModel):
    """
    If the audio output modality is requested, this object contains data
    about the audio response from the model. [Learn more](https://developers.openai.com/api/docs/guides/audio).
    """
    id: str
    data: str
    expires_at: int
    transcript: str
