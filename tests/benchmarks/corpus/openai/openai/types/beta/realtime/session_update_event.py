
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ...._models import BaseModel

class SessionClientSecretExpiresAfter(BaseModel):
    anchor: Literal['created_at']
    seconds: Optional[int] = None

class SessionClientSecret(BaseModel):
    expires_after: Optional[SessionClientSecretExpiresAfter] = None

class SessionInputAudioNoiseReduction(BaseModel):
    type: Optional[Literal['near_field', 'far_field']] = None

class SessionInputAudioTranscription(BaseModel):
    language: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None

class SessionTool(BaseModel):
    description: Optional[str] = None
    name: Optional[str] = None
    parameters: Optional[object] = None
    type: Optional[Literal['function']] = None

class SessionTracingTracingConfiguration(BaseModel):
    group_id: Optional[str] = None
    metadata: Optional[object] = None
    workflow_name: Optional[str] = None
SessionTracing: TypeAlias = Union[Literal['auto'], SessionTracingTracingConfiguration]

class SessionTurnDetection(BaseModel):
    create_response: Optional[bool] = None
    eagerness: Optional[Literal['low', 'medium', 'high', 'auto']] = None
    interrupt_response: Optional[bool] = None
    prefix_padding_ms: Optional[int] = None
    silence_duration_ms: Optional[int] = None
    threshold: Optional[float] = None
    type: Optional[Literal['server_vad', 'semantic_vad']] = None

class Session(BaseModel):
    client_secret: Optional[SessionClientSecret] = None
    input_audio_format: Optional[Literal['pcm16', 'g711_ulaw', 'g711_alaw']] = None
    input_audio_noise_reduction: Optional[SessionInputAudioNoiseReduction] = None
    input_audio_transcription: Optional[SessionInputAudioTranscription] = None
    instructions: Optional[str] = None
    max_response_output_tokens: Union[int, Literal['inf'], None] = None
    modalities: Optional[List[Literal['text', 'audio']]] = None
    model: Optional[Literal['gpt-realtime', 'gpt-realtime-2025-08-28', 'gpt-4o-realtime-preview', 'gpt-4o-realtime-preview-2024-10-01', 'gpt-4o-realtime-preview-2024-12-17', 'gpt-4o-realtime-preview-2025-06-03', 'gpt-4o-mini-realtime-preview', 'gpt-4o-mini-realtime-preview-2024-12-17']] = None
    output_audio_format: Optional[Literal['pcm16', 'g711_ulaw', 'g711_alaw']] = None
    speed: Optional[float] = None
    temperature: Optional[float] = None
    tool_choice: Optional[str] = None
    tools: Optional[List[SessionTool]] = None
    tracing: Optional[SessionTracing] = None
    turn_detection: Optional[SessionTurnDetection] = None
    voice: Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse'], None] = None

class SessionUpdateEvent(BaseModel):
    session: Session
    type: Literal['session.update']
    event_id: Optional[str] = None
