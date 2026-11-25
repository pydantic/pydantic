# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .beta_tool import BetaTool
from .beta_service_tier import BetaServiceTier
from .beta_response_input import BetaResponseInput
from .beta_response_prompt import BetaResponsePrompt
from .beta_tool_choice_mcp import BetaToolChoiceMcp
from .beta_tool_choice_shell import BetaToolChoiceShell
from .beta_tool_choice_types import BetaToolChoiceTypes
from .beta_tool_choice_custom import BetaToolChoiceCustom
from .beta_response_includable import BetaResponseIncludable
from .beta_tool_choice_allowed import BetaToolChoiceAllowed
from .beta_tool_choice_options import BetaToolChoiceOptions
from .beta_response_text_config import BetaResponseTextConfig
from .beta_tool_choice_function import BetaToolChoiceFunction
from .beta_tool_choice_apply_patch import BetaToolChoiceApplyPatch
from .beta_response_conversation_param import BetaResponseConversationParam

class ResponseCreateAccessPrograms(BaseModel):
    """Domain-specific access programs to use for this request."""
    cyber: Optional[Literal['standard', 'daybreak_blue', 'daybreak_red']] = None

class ResponseCreateContextManagement(BaseModel):
    type: str
    compact_threshold: Optional[int] = None
ResponseCreateConversation: TypeAlias = Union[str, BetaResponseConversationParam, None]

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

class ResponseCreateMultiAgent(BaseModel):
    """Configuration for server-hosted multi-agent execution."""
    enabled: bool
    max_concurrent_subagents: Optional[int] = None

class ResponseCreatePromptCacheOptions(BaseModel):
    """Options for prompt caching.

    Supported for `gpt-5.6` and later models. By default, OpenAI automatically chooses one implicit cache breakpoint. You can add explicit breakpoints to content blocks with `prompt_cache_breakpoint`. Each request can write up to four breakpoints. For cache matching, OpenAI considers up to the latest 80 breakpoints in the conversation, without a content-block lookback limit. Set `mode` to `explicit` to disable the implicit breakpoint. The `ttl` defaults to `30m`, which is currently the only supported value. See the [prompt caching guide](https://developers.openai.com/api/docs/guides/prompt-caching) for current details.
    """
    comparison_response_id: Optional[str] = None
    mode: Optional[Literal['implicit', 'explicit']] = None
    prewarm: Optional[bool] = None
    ttl: Optional[Literal['30m']] = None

class ResponseCreateReasoning(BaseModel):
    """
    Configuration options for
    [reasoning models](https://developers.openai.com/api/docs/guides/reasoning).
    """
    context: Optional[Literal['auto', 'current_turn', 'all_turns']] = None
    effort: Optional[Literal['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']] = None
    generate_summary: Optional[Literal['auto', 'concise', 'detailed']] = None
    mode: Union[str, Literal['standard', 'pro'], None] = None
    summary: Optional[Literal['auto', 'concise', 'detailed']] = None

class ResponseCreateStreamOptions(BaseModel):
    """Options for streaming responses. Only set this when you set `stream: true`."""
    include_obfuscation: Optional[bool] = None

class ResponseCreateToolChoiceBetaSpecificProgrammaticToolCallingParam(BaseModel):
    type: Literal['programmatic_tool_calling']
ResponseCreateToolChoice: TypeAlias = Union[BetaToolChoiceOptions, BetaToolChoiceAllowed, BetaToolChoiceTypes, BetaToolChoiceFunction, BetaToolChoiceMcp, BetaToolChoiceCustom, ResponseCreateToolChoiceBetaSpecificProgrammaticToolCallingParam, BetaToolChoiceApplyPatch, BetaToolChoiceShell]

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
    include: Optional[List[BetaResponseIncludable]] = None
    input: Union[str, BetaResponseInput, None] = None
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = None
    max_tool_calls: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None
    model: Union[Literal['gpt-6-astra', 'gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6-sol', 'gpt-6-luna', 'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-5.5', 'gpt-5.5-2026-04-23', 'gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-nano', 'gpt-5.4-mini-2026-03-17', 'gpt-5.4-nano-2026-03-17', 'gpt-5.3-chat-latest', 'gpt-5.2', 'gpt-5.2-2025-12-11', 'gpt-5.2-chat-latest', 'gpt-5.2-pro', 'gpt-5.2-pro-2025-12-11', 'gpt-5.1', 'gpt-5.1-2025-11-13', 'gpt-5.1-codex', 'gpt-5.1-mini', 'gpt-5.1-chat-latest', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'gpt-5-2025-08-07', 'gpt-5-mini-2025-08-07', 'gpt-5-nano-2025-08-07', 'gpt-5-chat-latest', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4.1-2025-04-14', 'gpt-4.1-mini-2025-04-14', 'gpt-4.1-nano-2025-04-14', 'o4-mini', 'o4-mini-2025-04-16', 'o3', 'o3-2025-04-16', 'o3-mini', 'o3-mini-2025-01-31', 'o1', 'o1-2024-12-17', 'o1-preview', 'o1-preview-2024-09-12', 'o1-mini', 'o1-mini-2024-09-12', 'gpt-4o', 'gpt-4o-2024-11-20', 'gpt-4o-2024-08-06', 'gpt-4o-2024-05-13', 'gpt-audio-mini', 'gpt-audio-mini-2025-12-15', 'gpt-4o-audio-preview', 'gpt-4o-audio-preview-2024-10-01', 'gpt-4o-audio-preview-2024-12-17', 'gpt-4o-audio-preview-2025-06-03', 'gpt-4o-mini-audio-preview', 'gpt-4o-mini-audio-preview-2024-12-17', 'gpt-4o-search-preview', 'gpt-4o-mini-search-preview', 'gpt-4o-search-preview-2025-03-11', 'gpt-4o-mini-search-preview-2025-03-11', 'chatgpt-4o-latest', 'codex-mini-latest', 'gpt-4o-mini', 'gpt-4o-mini-2024-07-18', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4-0125-preview', 'gpt-4-turbo-preview', 'gpt-4-1106-preview', 'gpt-4-vision-preview', 'gpt-4', 'gpt-4-0314', 'gpt-4-0613', 'gpt-4-32k', 'gpt-4-32k-0314', 'gpt-4-32k-0613', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0301', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-16k-0613', 'o1-pro', 'o1-pro-2025-03-19', 'o3-pro', 'o3-pro-2025-06-10', 'o3-deep-research', 'o3-deep-research-2025-06-26', 'o4-mini-deep-research', 'o4-mini-deep-research-2025-06-26', 'computer-use-preview', 'computer-use-preview-2025-03-11', 'gpt-5.5-pro', 'gpt-5.5-pro-2026-04-23', 'gpt-5-codex', 'gpt-5-pro', 'gpt-5-pro-2025-10-06', 'gpt-5.1-codex-max', 'gpt-daybreak-blue-latest', 'gpt-daybreak-red-latest', 'gpt-5.6-cyber', 'gpt-rosalind-research'], str, None] = None
    moderation: Optional[ResponseCreateModeration] = None
    multi_agent: Optional[ResponseCreateMultiAgent] = None
    parallel_tool_calls: Optional[bool] = None
    previous_response_id: Optional[str] = None
    prompt: Optional[BetaResponsePrompt] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_options: Optional[ResponseCreatePromptCacheOptions] = None
    prompt_cache_retention: Optional[Literal['in_memory', '24h']] = None
    reasoning: Optional[ResponseCreateReasoning] = None
    safety_identifier: Optional[str] = None
    service_tier: Optional[BetaServiceTier] = None
    store: Optional[bool] = None
    stream: Optional[bool] = None
    stream_id: Optional[str] = None
    stream_options: Optional[ResponseCreateStreamOptions] = None
    temperature: Optional[float] = None
    text: Optional[BetaResponseTextConfig] = None
    tool_choice: Optional[ResponseCreateToolChoice] = None
    tools: Optional[List[BetaTool]] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None
    truncation: Optional[Literal['auto', 'disabled']] = None
    user: Optional[str] = None
