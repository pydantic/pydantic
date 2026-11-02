# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .noise_reduction_type import NoiseReductionType

class AudioInputNoiseReduction(BaseModel):
    """Optional input noise reduction."""
    type: NoiseReductionType

class AudioInputTranscription(BaseModel):
    """Optional source-language transcription.

    When configured, the server emits
    `session.input_transcript.delta` events. Translation itself still runs from
    the input audio stream.
    """
    model: str

class AudioInput(BaseModel):
    noise_reduction: Optional[AudioInputNoiseReduction] = None
    transcription: Optional[AudioInputTranscription] = None

class AudioOutput(BaseModel):
    language: Optional[str] = None

class Audio(BaseModel):
    """Configuration for translation input and output audio."""
    input: Optional[AudioInput] = None
    output: Optional[AudioOutput] = None

class RealtimeTranslationSession(BaseModel):
    """A Realtime translation session.

    Translation sessions continuously translate input
    audio into the configured output language.
    """
    id: str
    audio: Audio
    expires_at: int
    model: str
    type: Literal['translation']
