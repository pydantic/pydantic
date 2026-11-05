# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from .tool import Tool
from ..._models import BaseModel
from .service_tier import ServiceTier
from .response_input import ResponseInput
from .response_prompt import ResponsePrompt
from .tool_choice_mcp import ToolChoiceMcp
from ..shared.metadata import Metadata
from ..shared.reasoning import Reasoning
from .tool_choice_shell import ToolChoiceShell
from .tool_choice_types import ToolChoiceTypes
from .tool_choice_custom import ToolChoiceCustom
from .response_includable import ResponseIncludable
from .tool_choice_allowed import ToolChoiceAllowed
from .tool_choice_options import ToolChoiceOptions
from .response_text_config import ResponseTextConfig
from .tool_choice_function import ToolChoiceFunction
from ..shared.responses_model import ResponsesModel
from .tool_choice_apply_patch import ToolChoiceApplyPatch
from .response_conversation_param import ResponseConversationParam

class ResponseCreateAccessPrograms(BaseModel):
    """Domain-specific access programs to use for this request."""
    cyber: Optional[Literal['standard', 'daybreak_blue', 'daybreak_red']] = None

class ResponseCreateContextManagement(BaseModel):
    type: str
    compact_threshold: Optional[int] = None
ResponseCreateConversation: TypeAlias = Union[str, ResponseConversationParam, None]

class ResponseCreateModerationPolicyInput(BaseModel):
    """The moderation policy for the response input."""
    mode: Literal['score', 'block']

class ResponseCreateModerationPolicyOutput(BaseModel):
    """The moderation policy for the response output."""
    mode: Literal['score', 'block']

class ResponseCreateModerationPolicy(BaseModel):
    """The policy to apply to moderated response input and output."""
    input: Optional[ResponseCreateModerationPolicyInput] = None
    output: Optional[ResponseCreateModerationPolicyOutput] = None

class ResponseCreateModeration(BaseModel):
    """Configuration for running moderation on the input and output of this response."""
    model: str
    policy: Optional[ResponseCreateModerationPolicy] = None

class ResponseCreatePromptCacheOptions(BaseModel):
    """Options for prompt caching.

    Supported for `gpt-5.6` and later models. By default, OpenAI automatically chooses one implicit cache breakpoint. You can add explicit breakpoints to content blocks with `prompt_cache_breakpoint`. Each request can write up to four breakpoints. For cache matching, OpenAI considers up to the latest 80 breakpoints in the conversation, without a content-block lookback limit. Set `mode` to `explicit` to disable the implicit breakpoint. The `ttl` defaults to `30m`, which is currently the only supported value. See the [prompt caching guide](https://developers.openai.com/api/docs/guides/prompt-caching) for current details.
    """
    comparison_response_id: Optional[str] = None
    mode: Optional[Literal['implicit', 'explicit']] = None
    prewarm: Optional[bool] = None
    ttl: Optional[Literal['30m']] = None

class ResponseCreateStreamOptions(BaseModel):
    """Options for streaming responses. Only set this when you set `stream: true`."""
    include_obfuscation: Optional[bool] = None

class ResponseCreateToolChoiceSpecificProgrammaticToolCallingParam(BaseModel):
    type: Literal['programmatic_tool_calling']
ResponseCreateToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceAllowed, ToolChoiceTypes, ToolChoiceFunction, ToolChoiceMcp, ToolChoiceCustom, ResponseCreateToolChoiceSpecificProgrammaticToolCallingParam, ToolChoiceApplyPatch, ToolChoiceShell]

class ResponseCreate(BaseModel):
    """
    Client event for creating a response over a persistent WebSocket connection.
    This payload uses the same top-level fields as `POST /v1/responses`, plus
    WebSocket-only envelope metadata.

    Notes:
    - `stream` is implicit over WebSocket and should not be sent.
    - `background` is not supported over WebSocket.
    - `stream_id` is WebSocket-only and is not part of `POST /v1/responses`.
    """
    type: Literal['response.create']
    access_programs: Optional[ResponseCreateAccessPrograms] = None
    background: Optional[bool] = None
    context_management: Optional[List[ResponseCreateContextManagement]] = None
    conversation: Optional[ResponseCreateConversation] = None
    include: Optional[List[ResponseIncludable]] = None
    input: Union[str, ResponseInput, None] = None
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = None
    max_tool_calls: Optional[int] = None
    metadata: Optional[Metadata] = None
    model: Optional[ResponsesModel] = None
    moderation: Optional[ResponseCreateModeration] = None
    parallel_tool_calls: Optional[bool] = None
    previous_response_id: Optional[str] = None
    prompt: Optional[ResponsePrompt] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_options: Optional[ResponseCreatePromptCacheOptions] = None
    prompt_cache_retention: Optional[Literal['in_memory', '24h']] = None
    reasoning: Optional[Reasoning] = None
    safety_identifier: Optional[str] = None
    service_tier: Optional[ServiceTier] = None
    store: Optional[bool] = None
    stream: Optional[bool] = None
    stream_id: Optional[str] = None
    stream_options: Optional[ResponseCreateStreamOptions] = None
    temperature: Optional[float] = None
    text: Optional[ResponseTextConfig] = None
    tool_choice: Optional[ResponseCreateToolChoice] = None
    tools: Optional[List[Tool]] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None
    truncation: Optional[Literal['auto', 'disabled']] = None
    user: Optional[str] = None
