
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ...._models import BaseModel

class InputAudioNoiseReduction(BaseModel):
    type: Optional[Literal['near_field', 'far_field']] = None

class InputAudioTranscription(BaseModel):
    language: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None

class Tool(BaseModel):
    description: Optional[str] = None
    name: Optional[str] = None
    parameters: Optional[object] = None
    type: Optional[Literal['function']] = None

class TracingTracingConfiguration(BaseModel):
    group_id: Optional[str] = None
    metadata: Optional[object] = None
    workflow_name: Optional[str] = None
Tracing: TypeAlias = Union[Literal['auto'], TracingTracingConfiguration]

class TurnDetection(BaseModel):
    create_response: Optional[bool] = None
    eagerness: Optional[Literal['low', 'medium', 'high', 'auto']] = None
    interrupt_response: Optional[bool] = None
    prefix_padding_ms: Optional[int] = None
    silence_duration_ms: Optional[int] = None
    threshold: Optional[float] = None
    type: Optional[Literal['server_vad', 'semantic_vad']] = None

class Session(BaseModel):
    id: Optional[str] = None
    input_audio_format: Optional[Literal['pcm16', 'g711_ulaw', 'g711_alaw']] = None
    input_audio_noise_reduction: Optional[InputAudioNoiseReduction] = None
    input_audio_transcription: Optional[InputAudioTranscription] = None
    instructions: Optional[str] = None
    max_response_output_tokens: Union[int, Literal['inf'], None] = None
    modalities: Optional[List[Literal['text', 'audio']]] = None
    model: Optional[Literal['gpt-realtime', 'gpt-realtime-2025-08-28', 'gpt-4o-realtime-preview', 'gpt-4o-realtime-preview-2024-10-01', 'gpt-4o-realtime-preview-2024-12-17', 'gpt-4o-realtime-preview-2025-06-03', 'gpt-4o-mini-realtime-preview', 'gpt-4o-mini-realtime-preview-2024-12-17']] = None
    output_audio_format: Optional[Literal['pcm16', 'g711_ulaw', 'g711_alaw']] = None
    speed: Optional[float] = None
    temperature: Optional[float] = None
    tool_choice: Optional[str] = None
    tools: Optional[List[Tool]] = None
    tracing: Optional[Tracing] = None
    turn_detection: Optional[TurnDetection] = None
    voice: Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse'], None] = None
