# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from ..shared.metadata import Metadata
from ..completion_usage import CompletionUsage
from .chat_completion_message import ChatCompletionMessage
from .chat_completion_token_logprob import ChatCompletionTokenLogprob

class ChoiceLogprobs(BaseModel):
    """Log probability information for the choice."""
    content: Optional[List[ChatCompletionTokenLogprob]] = None
    refusal: Optional[List[ChatCompletionTokenLogprob]] = None

class Choice(BaseModel):
    finish_reason: Literal['stop', 'length', 'tool_calls', 'content_filter', 'function_call']
    index: int
    logprobs: Optional[ChoiceLogprobs] = None
    message: ChatCompletionMessage

class ModerationInputModerationResultsResult(BaseModel):
    """A moderation result produced for the response input or output."""
    categories: Dict[str, bool]
    category_applied_input_types: Dict[str, List[Literal['text', 'image']]]
    category_scores: Dict[str, float]
    flagged: bool
    model: str
    type: Literal['moderation_result']

class ModerationInputModerationResults(BaseModel):
    """Successful moderation results for the request input or generated output."""
    model: str
    results: List[ModerationInputModerationResultsResult]
    type: Literal['moderation_results']

class ModerationInputError(BaseModel):
    """An error produced while attempting moderation."""
    code: str
    message: str
    type: Literal['error']
ModerationInput: TypeAlias = Annotated[Union[ModerationInputModerationResults, ModerationInputError], PropertyInfo(discriminator='type')]

class ModerationOutputModerationResultsResult(BaseModel):
    """A moderation result produced for the response input or output."""
    categories: Dict[str, bool]
    category_applied_input_types: Dict[str, List[Literal['text', 'image']]]
    category_scores: Dict[str, float]
    flagged: bool
    model: str
    type: Literal['moderation_result']

class ModerationOutputModerationResults(BaseModel):
    """Successful moderation results for the request input or generated output."""
    model: str
    results: List[ModerationOutputModerationResultsResult]
    type: Literal['moderation_results']

class ModerationOutputError(BaseModel):
    """An error produced while attempting moderation."""
    code: str
    message: str
    type: Literal['error']
ModerationOutput: TypeAlias = Annotated[Union[ModerationOutputModerationResults, ModerationOutputError], PropertyInfo(discriminator='type')]

class Moderation(BaseModel):
    """
    Moderation results for the request input and generated output, if moderated
    completions were requested.
    """
    input: ModerationInput
    output: ModerationOutput

class ChatCompletion(BaseModel):
    """
    Represents a chat completion response returned by model, based on the provided input.
    """
    id: str
    choices: List[Choice]
    created: int
    model: str
    object: Literal['chat.completion']
    metadata: Optional[Metadata] = None
    moderation: Optional[Moderation] = None
    service_tier: Optional[Literal['auto', 'default', 'flex', 'scale', 'priority', 'fast']] = None
    system_fingerprint: Optional[str] = None
    usage: Optional[CompletionUsage] = None
