# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .tool import Tool
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .service_tier import ServiceTier
from .response_error import ResponseError
from .response_usage import ResponseUsage
from .response_prompt import ResponsePrompt
from .response_status import ResponseStatus
from .tool_choice_mcp import ToolChoiceMcp
from ..shared.metadata import Metadata
from ..shared.reasoning import Reasoning
from .tool_choice_shell import ToolChoiceShell
from .tool_choice_types import ToolChoiceTypes
from .tool_choice_custom import ToolChoiceCustom
from .response_input_item import ResponseInputItem
from .tool_choice_allowed import ToolChoiceAllowed
from .tool_choice_options import ToolChoiceOptions
from .response_output_item import ResponseOutputItem
from .response_text_config import ResponseTextConfig
from .tool_choice_function import ToolChoiceFunction
from ..shared.responses_model import ResponsesModel
from .tool_choice_apply_patch import ToolChoiceApplyPatch

class AccessPrograms(BaseModel):
    cyber: Literal['standard', 'daybreak_blue', 'daybreak_red']

class IncompleteDetails(BaseModel):
    """Details about why the response is incomplete."""
    reason: Optional[Literal['max_output_tokens', 'max_messages', 'content_filter', 'steered']] = None

class ToolChoiceSpecificProgrammaticToolCallingParam(BaseModel):
    type: Literal['programmatic_tool_calling']
ToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceAllowed, ToolChoiceTypes, ToolChoiceFunction, ToolChoiceMcp, ToolChoiceCustom, ToolChoiceSpecificProgrammaticToolCallingParam, ToolChoiceApplyPatch, ToolChoiceShell]

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

class Response(BaseModel):
    id: str
    access_programs: Optional[AccessPrograms] = None
    created_at: float
    error: Optional[ResponseError] = None
    incomplete_details: Optional[IncompleteDetails] = None
    instructions: Union[str, List[ResponseInputItem], None] = None
    metadata: Optional[Metadata] = None
    model: ResponsesModel
    object: Literal['response']
    output: List[ResponseOutputItem]
    parallel_tool_calls: bool
    temperature: Optional[float] = None
    tool_choice: ToolChoice
    tools: List[Tool]
    top_p: Optional[float] = None
    background: Optional[bool] = None
    completed_at: Optional[float] = None
    conversation: Optional[Conversation] = None
    max_output_tokens: Optional[int] = None
    max_tool_calls: Optional[int] = None
    moderation: Optional[Moderation] = None
    previous_response_id: Optional[str] = None
    prompt: Optional[ResponsePrompt] = None
    prompt_cache_diagnostics: Optional[PromptCacheDiagnostics] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_options: Optional[PromptCacheOptions] = None
    prompt_cache_retention: Optional[Literal['in_memory', '24h']] = None
    reasoning: Optional[Reasoning] = None
    safety_identifier: Optional[str] = None
    service_tier: Optional[ServiceTier] = None
    status: Optional[ResponseStatus] = None
    text: Optional[ResponseTextConfig] = None
    tool_usage: Optional[ToolUsage] = None
    top_logprobs: Optional[int] = None
    truncation: Optional[Literal['auto', 'disabled']] = None
    usage: Optional[ResponseUsage] = None
    user: Optional[str] = None
