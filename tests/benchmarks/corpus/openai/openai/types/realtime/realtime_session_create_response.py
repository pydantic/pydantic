# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .realtime_reasoning import RealtimeReasoning
from .audio_transcription import AudioTranscription
from .realtime_truncation import RealtimeTruncation
from .noise_reduction_type import NoiseReductionType
from .realtime_audio_formats import RealtimeAudioFormats
from .realtime_function_tool import RealtimeFunctionTool
from ..responses.response_prompt import ResponsePrompt
from ..responses.tool_choice_mcp import ToolChoiceMcp
from ..responses.tool_choice_options import ToolChoiceOptions
from ..responses.tool_choice_function import ToolChoiceFunction

class AudioInputNoiseReduction(BaseModel):
    """Configuration for input audio noise reduction.

    This can be set to `null` to turn off.
    Noise reduction filters audio added to the input audio buffer before it is sent to VAD and the model.
    Filtering the audio can improve VAD and turn detection accuracy (reducing false positives) and model performance by improving perception of the input audio.
    """
    type: Optional[NoiseReductionType] = None

class AudioInputTurnDetectionServerVad(BaseModel):
    """
    Server-side voice activity detection (VAD) which flips on when user speech is detected and off after a period of silence.
    """
    type: Literal['server_vad']
    create_response: Optional[bool] = None
    idle_timeout_ms: Optional[int] = None
    interrupt_response: Optional[bool] = None
    prefix_padding_ms: Optional[int] = None
    silence_duration_ms: Optional[int] = None
    threshold: Optional[float] = None

class AudioInputTurnDetectionSemanticVad(BaseModel):
    """
    Server-side semantic turn detection which uses a model to determine when the user has finished speaking.
    """
    type: Literal['semantic_vad']
    create_response: Optional[bool] = None
    eagerness: Optional[Literal['low', 'medium', 'high', 'auto']] = None
    interrupt_response: Optional[bool] = None
AudioInputTurnDetection: TypeAlias = Annotated[Union[AudioInputTurnDetectionServerVad, AudioInputTurnDetectionSemanticVad, None], PropertyInfo(discriminator='type')]

class AudioInput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    noise_reduction: Optional[AudioInputNoiseReduction] = None
    transcription: Optional[AudioTranscription] = None
    turn_detection: Optional[AudioInputTurnDetection] = None

class AudioOutput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    speed: Optional[float] = None
    voice: Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar'], None] = None

class Audio(BaseModel):
    """Configuration for input and output audio."""
    input: Optional[AudioInput] = None
    output: Optional[AudioOutput] = None
ToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceFunction, ToolChoiceMcp]

class ToolMcpToolAllowedToolsMcpToolFilter(BaseModel):
    """A filter object to specify which tools are allowed."""
    read_only: Optional[bool] = None
    tool_names: Optional[List[str]] = None
ToolMcpToolAllowedTools: TypeAlias = Union[List[str], ToolMcpToolAllowedToolsMcpToolFilter, None]

class ToolMcpToolRequireApprovalMcpToolApprovalFilterAlways(BaseModel):
    """A filter object to specify which tools are allowed."""
    read_only: Optional[bool] = None
    tool_names: Optional[List[str]] = None

class ToolMcpToolRequireApprovalMcpToolApprovalFilterNever(BaseModel):
    """A filter object to specify which tools are allowed."""
    read_only: Optional[bool] = None
    tool_names: Optional[List[str]] = None

class ToolMcpToolRequireApprovalMcpToolApprovalFilter(BaseModel):
    """Specify which of the MCP server's tools require approval.

    Can be
    `always`, `never`, or a filter object associated with tools
    that require approval.
    """
    always: Optional[ToolMcpToolRequireApprovalMcpToolApprovalFilterAlways] = None
    never: Optional[ToolMcpToolRequireApprovalMcpToolApprovalFilterNever] = None
ToolMcpToolRequireApproval: TypeAlias = Union[ToolMcpToolRequireApprovalMcpToolApprovalFilter, Literal['always', 'never'], None]

class ToolMcpTool(BaseModel):
    """
    Give the model access to additional tools via remote Model Context Protocol
    (MCP) servers. [Learn more about MCP](https://developers.openai.com/api/docs/guides/tools-connectors-mcp).
    """
    server_label: str
    type: Literal['mcp']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
    allowed_tools: Optional[ToolMcpToolAllowedTools] = None
    authorization: Optional[str] = None
    connector_id: Optional[Literal['connector_dropbox', 'connector_gmail', 'connector_googlecalendar', 'connector_googledrive', 'connector_microsoftteams', 'connector_outlookcalendar', 'connector_outlookemail', 'connector_sharepoint']] = None
    defer_loading: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    require_approval: Optional[ToolMcpToolRequireApproval] = None
    server_description: Optional[str] = None
    server_url: Optional[str] = None
    tunnel_id: Optional[str] = None
Tool: TypeAlias = Union[RealtimeFunctionTool, ToolMcpTool]

class TracingTracingConfiguration(BaseModel):
    """Granular configuration for tracing."""
    group_id: Optional[str] = None
    metadata: Optional[object] = None
    workflow_name: Optional[str] = None
Tracing: TypeAlias = Union[Literal['auto'], TracingTracingConfiguration, None]

class RealtimeSessionCreateResponse(BaseModel):
    """A Realtime session configuration object."""
    id: str
    object: Literal['realtime.session']
    type: Literal['realtime']
    audio: Optional[Audio] = None
    expires_at: Optional[int] = None
    include: Optional[List[Literal['item.input_audio_transcription.logprobs']]] = None
    instructions: Optional[str] = None
    max_output_tokens: Union[int, Literal['inf'], None] = None
    model: Union[str, Literal['gpt-realtime', 'gpt-realtime-1.5', 'gpt-realtime-2', 'gpt-realtime-2.1', 'gpt-realtime-2.1-mini', 'gpt-realtime-2025-08-28', 'gpt-4o-realtime-preview', 'gpt-4o-realtime-preview-2024-10-01', 'gpt-4o-realtime-preview-2024-12-17', 'gpt-4o-realtime-preview-2025-06-03', 'gpt-4o-mini-realtime-preview', 'gpt-4o-mini-realtime-preview-2024-12-17', 'gpt-realtime-mini', 'gpt-realtime-mini-2025-10-06', 'gpt-realtime-mini-2025-12-15', 'gpt-audio-1.5', 'gpt-audio-mini', 'gpt-audio-mini-2025-10-06', 'gpt-audio-mini-2025-12-15'], None] = None
    output_modalities: Optional[List[Literal['text', 'audio']]] = None
    prompt: Optional[ResponsePrompt] = None
    reasoning: Optional[RealtimeReasoning] = None
    tool_choice: Optional[ToolChoice] = None
    tools: Optional[List[Tool]] = None
    tracing: Optional[Tracing] = None
    truncation: Optional[RealtimeTruncation] = None
