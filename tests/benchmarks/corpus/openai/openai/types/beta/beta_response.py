# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_tool import BetaTool
from .beta_service_tier import BetaServiceTier
from .beta_response_error import BetaResponseError
from .beta_response_usage import BetaResponseUsage
from .beta_response_prompt import BetaResponsePrompt
from .beta_response_status import BetaResponseStatus
from .beta_tool_choice_mcp import BetaToolChoiceMcp
from .beta_tool_choice_shell import BetaToolChoiceShell
from .beta_tool_choice_types import BetaToolChoiceTypes
from .beta_tool_choice_custom import BetaToolChoiceCustom
from .beta_response_input_item import BetaResponseInputItem
from .beta_tool_choice_allowed import BetaToolChoiceAllowed
from .beta_tool_choice_options import BetaToolChoiceOptions
from .beta_response_output_item import BetaResponseOutputItem
from .beta_response_text_config import BetaResponseTextConfig
from .beta_tool_choice_function import BetaToolChoiceFunction
from .beta_tool_choice_apply_patch import BetaToolChoiceApplyPatch

class AccessPrograms(BaseModel):
    cyber: Literal['standard', 'daybreak_blue', 'daybreak_red']

class IncompleteDetails(BaseModel):
    """Details about why the response is incomplete."""
    reason: Optional[Literal['max_output_tokens', 'max_messages', 'content_filter', 'steered']] = None

class ToolChoiceBetaSpecificProgrammaticToolCallingParam(BaseModel):
    type: Literal['programmatic_tool_calling']
ToolChoice: TypeAlias = Union[BetaToolChoiceOptions, BetaToolChoiceAllowed, BetaToolChoiceTypes, BetaToolChoiceFunction, BetaToolChoiceMcp, BetaToolChoiceCustom, ToolChoiceBetaSpecificProgrammaticToolCallingParam, BetaToolChoiceApplyPatch, BetaToolChoiceShell]

class Conversation(BaseModel):
    """The conversation that this response belonged to.

    Input items and output items from this response were automatically added to this conversation.
    """
    id: str

class ModerationInputModerationResult(BaseModel):
    """A moderation result produced for the response input or output."""
    categories: Dict[str, bool]
    category_applied_input_types: Dict[str, List[Literal['text', 'image']]]
    category_scores: Dict[str, float]
    flagged: bool
    model: str
    type: Literal['moderation_result']

class ModerationInputError(BaseModel):
    """An error produced while attempting moderation for the response input or output."""
    code: str
    message: str
    type: Literal['error']
ModerationInput: TypeAlias = Annotated[Union[ModerationInputModerationResult, ModerationInputError], PropertyInfo(discriminator='type')]

class ModerationOutputModerationResult(BaseModel):
    """A moderation result produced for the response input or output."""
    categories: Dict[str, bool]
    category_applied_input_types: Dict[str, List[Literal['text', 'image']]]
    category_scores: Dict[str, float]
    flagged: bool
    model: str
    type: Literal['moderation_result']

class ModerationOutputError(BaseModel):
    """An error produced while attempting moderation for the response input or output."""
    code: str
    message: str
    type: Literal['error']
ModerationOutput: TypeAlias = Annotated[Union[ModerationOutputModerationResult, ModerationOutputError], PropertyInfo(discriminator='type')]

class Moderation(BaseModel):
    """
    Moderation results for the response input and output, if moderated completions were requested.
    """
    input: ModerationInput
    output: ModerationOutput

class PromptCacheDiagnosticsCacheMiss(BaseModel):
    cache_missed_tokens: int
    reason: Literal['model_changed', 'prompt_cache_key_changed', 'tools_changed', 'text_format_changed', 'reasoning_effort_changed', 'verbosity_changed', 'context_compacted', 'input_changed', 'service_tier_changed']
    type: Literal['cache_miss']
    comparison_reusable_tokens: Optional[int] = None

class PromptCacheDiagnosticsCacheHit(BaseModel):
    type: Literal['cache_hit']

class PromptCacheDiagnosticsComparisonResponseNotFound(BaseModel):
    type: Literal['comparison_response_not_found']

class PromptCacheDiagnosticsUnavailable(BaseModel):
    type: Literal['unavailable']
PromptCacheDiagnostics: TypeAlias = Annotated[Union[PromptCacheDiagnosticsCacheMiss, PromptCacheDiagnosticsCacheHit, PromptCacheDiagnosticsComparisonResponseNotFound, PromptCacheDiagnosticsUnavailable], PropertyInfo(discriminator='type')]

class PromptCacheOptions(BaseModel):
    """The prompt-caching options that were applied to the response.

    Supported for `gpt-5.6` and later models.
    """
    mode: Literal['implicit', 'explicit']
    ttl: Literal['30m']
    comparison_response_id: Optional[str] = None

class Reasoning(BaseModel):
    """
    Configuration options for
    [reasoning models](https://developers.openai.com/api/docs/guides/reasoning).
    """
    context: Optional[Literal['auto', 'current_turn', 'all_turns']] = None
    effort: Optional[Literal['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']] = None
    generate_summary: Optional[Literal['auto', 'concise', 'detailed']] = None
    mode: Union[str, Literal['standard', 'pro'], None] = None
    summary: Optional[Literal['auto', 'concise', 'detailed']] = None

class ToolUsageImageGenInputTokensDetails(BaseModel):
    """The input tokens detailed information for the image generation."""
    image_tokens: int
    text_tokens: int

class ToolUsageImageGenCachedTokensDetails(BaseModel):
    cached_image_tokens: int
    cached_text_tokens: int

class ToolUsageImageGenOutputTokensDetails(BaseModel):
    """The output token details for the image generation."""
    image_tokens: int
    text_tokens: int

class ToolUsageImageGen(BaseModel):
    """Aggregated usage statistics for image generation tool calls."""
    input_tokens: int
    input_tokens_details: ToolUsageImageGenInputTokensDetails
    output_tokens: int
    total_tokens: int
    cached_tokens: Optional[int] = None
    cached_tokens_details: Optional[ToolUsageImageGenCachedTokensDetails] = None
    output_tokens_details: Optional[ToolUsageImageGenOutputTokensDetails] = None

class ToolUsageWebSearch(BaseModel):
    """Aggregated billable usage statistics for web search tool calls."""
    num_requests: int

class ToolUsage(BaseModel):
    """Usage reported by hosted tools, separate from base model `usage`.

    The field
    can be omitted when tool usage is unavailable. When present, tool families
    with no recorded usage have zero counts.

    `image_gen` sums available token counts across image generation calls.
    Calls with missing or incomplete usage records may be skipped. Output
    token details and cached input counts can be omitted. An omitted cache
    count means cache usage is unknown.

    `web_search.num_requests` counts billable searches. Discounted searches
    and actions such as opening a page are excluded. Use billing records to
    reconcile final charges.
    """
    image_gen: ToolUsageImageGen
    web_search: ToolUsageWebSearch

class BetaResponse(BaseModel):
    id: str
    access_programs: Optional[AccessPrograms] = None
    created_at: float
    error: Optional[BetaResponseError] = None
    incomplete_details: Optional[IncompleteDetails] = None
    instructions: Union[str, List[BetaResponseInputItem], None] = None
    metadata: Optional[Dict[str, str]] = None
    model: Union[Literal['gpt-6-astra', 'gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6-sol', 'gpt-6-luna', 'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-5.5', 'gpt-5.5-2026-04-23', 'gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-nano', 'gpt-5.4-mini-2026-03-17', 'gpt-5.4-nano-2026-03-17', 'gpt-5.3-chat-latest', 'gpt-5.2', 'gpt-5.2-2025-12-11', 'gpt-5.2-chat-latest', 'gpt-5.2-pro', 'gpt-5.2-pro-2025-12-11', 'gpt-5.1', 'gpt-5.1-2025-11-13', 'gpt-5.1-codex', 'gpt-5.1-mini', 'gpt-5.1-chat-latest', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'gpt-5-2025-08-07', 'gpt-5-mini-2025-08-07', 'gpt-5-nano-2025-08-07', 'gpt-5-chat-latest', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4.1-2025-04-14', 'gpt-4.1-mini-2025-04-14', 'gpt-4.1-nano-2025-04-14', 'o4-mini', 'o4-mini-2025-04-16', 'o3', 'o3-2025-04-16', 'o3-mini', 'o3-mini-2025-01-31', 'o1', 'o1-2024-12-17', 'o1-preview', 'o1-preview-2024-09-12', 'o1-mini', 'o1-mini-2024-09-12', 'gpt-4o', 'gpt-4o-2024-11-20', 'gpt-4o-2024-08-06', 'gpt-4o-2024-05-13', 'gpt-audio-mini', 'gpt-audio-mini-2025-12-15', 'gpt-4o-audio-preview', 'gpt-4o-audio-preview-2024-10-01', 'gpt-4o-audio-preview-2024-12-17', 'gpt-4o-audio-preview-2025-06-03', 'gpt-4o-mini-audio-preview', 'gpt-4o-mini-audio-preview-2024-12-17', 'gpt-4o-search-preview', 'gpt-4o-mini-search-preview', 'gpt-4o-search-preview-2025-03-11', 'gpt-4o-mini-search-preview-2025-03-11', 'chatgpt-4o-latest', 'codex-mini-latest', 'gpt-4o-mini', 'gpt-4o-mini-2024-07-18', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4-0125-preview', 'gpt-4-turbo-preview', 'gpt-4-1106-preview', 'gpt-4-vision-preview', 'gpt-4', 'gpt-4-0314', 'gpt-4-0613', 'gpt-4-32k', 'gpt-4-32k-0314', 'gpt-4-32k-0613', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0301', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-16k-0613', 'o1-pro', 'o1-pro-2025-03-19', 'o3-pro', 'o3-pro-2025-06-10', 'o3-deep-research', 'o3-deep-research-2025-06-26', 'o4-mini-deep-research', 'o4-mini-deep-research-2025-06-26', 'computer-use-preview', 'computer-use-preview-2025-03-11', 'gpt-5.5-pro', 'gpt-5.5-pro-2026-04-23', 'gpt-5-codex', 'gpt-5-pro', 'gpt-5-pro-2025-10-06', 'gpt-5.1-codex-max', 'gpt-daybreak-blue-latest', 'gpt-daybreak-red-latest', 'gpt-5.6-cyber', 'gpt-rosalind-research'], str]
    object: Literal['response']
    output: List[BetaResponseOutputItem]
    parallel_tool_calls: bool
    temperature: Optional[float] = None
    tool_choice: ToolChoice
    tools: List[BetaTool]
    top_p: Optional[float] = None
    background: Optional[bool] = None
    completed_at: Optional[float] = None
    conversation: Optional[Conversation] = None
    max_output_tokens: Optional[int] = None
    max_tool_calls: Optional[int] = None
    moderation: Optional[Moderation] = None
    previous_response_id: Optional[str] = None
    prompt: Optional[BetaResponsePrompt] = None
    prompt_cache_diagnostics: Optional[PromptCacheDiagnostics] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_options: Optional[PromptCacheOptions] = None
    prompt_cache_retention: Optional[Literal['in_memory', '24h']] = None
    reasoning: Optional[Reasoning] = None
    safety_identifier: Optional[str] = None
    service_tier: Optional[BetaServiceTier] = None
    status: Optional[BetaResponseStatus] = None
    text: Optional[BetaResponseTextConfig] = None
    tool_usage: Optional[ToolUsage] = None
    top_logprobs: Optional[int] = None
    truncation: Optional[Literal['auto', 'disabled']] = None
    usage: Optional[BetaResponseUsage] = None
    user: Optional[str] = None
