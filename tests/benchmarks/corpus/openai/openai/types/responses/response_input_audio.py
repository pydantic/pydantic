# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudio(BaseModel):
    data: str
    format: Literal['mp3', 'wav']

class ResponseInputAudio(BaseModel):
    """An audio input to the model."""
    input_audio: InputAudio
    type: Literal['input_audio']
