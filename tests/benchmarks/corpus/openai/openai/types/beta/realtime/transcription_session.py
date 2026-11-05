
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ClientSecret(BaseModel):
    expires_at: int
    value: str

class InputAudioTranscription(BaseModel):
    language: Optional[str] = None
    model: Optional[Literal['gpt-4o-transcribe', 'gpt-4o-mini-transcribe', 'whisper-1']] = None
    prompt: Optional[str] = None

class TurnDetection(BaseModel):
    prefix_padding_ms: Optional[int] = None
    silence_duration_ms: Optional[int] = None
    threshold: Optional[float] = None
    type: Optional[str] = None

class TranscriptionSession(BaseModel):
    client_secret: ClientSecret
    input_audio_format: Optional[str] = None
    input_audio_transcription: Optional[InputAudioTranscription] = None
    modalities: Optional[List[Literal['text', 'audio']]] = None
    turn_detection: Optional[TurnDetection] = None
