# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from ..shared.metadata import Metadata
from .conversation_item import ConversationItem
from .realtime_reasoning import RealtimeReasoning
from .realtime_function_tool import RealtimeFunctionTool
from ..responses.response_prompt import ResponsePrompt
from ..responses.tool_choice_mcp import ToolChoiceMcp
from ..responses.tool_choice_options import ToolChoiceOptions
from ..responses.tool_choice_function import ToolChoiceFunction
from .realtime_response_create_mcp_tool import RealtimeResponseCreateMcpTool
from .realtime_response_create_audio_output import RealtimeResponseCreateAudioOutput
ToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceFunction, ToolChoiceMcp]
Tool: TypeAlias = Union[RealtimeFunctionTool, RealtimeResponseCreateMcpTool]

class RealtimeResponseCreateParams(BaseModel):
    """Create a new Realtime response with these parameters"""
    audio: Optional[RealtimeResponseCreateAudioOutput] = None
    conversation: Union[str, Literal['auto', 'none'], None] = None
    input: Optional[List[ConversationItem]] = None
    instructions: Optional[str] = None
    max_output_tokens: Union[int, Literal['inf'], None] = None
    metadata: Optional[Metadata] = None
    output_modalities: Optional[List[Literal['text', 'audio']]] = None
    parallel_tool_calls: Optional[bool] = None
    prompt: Optional[ResponsePrompt] = None
    reasoning: Optional[RealtimeReasoning] = None
    tool_choice: Optional[ToolChoice] = None
    tools: Optional[List[Tool]] = None
