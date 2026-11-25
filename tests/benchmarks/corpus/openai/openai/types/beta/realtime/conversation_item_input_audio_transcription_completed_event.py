
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ...._models import BaseModel

class UsageTranscriptTextUsageTokensInputTokenDetails(BaseModel):
    audio_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class UsageTranscriptTextUsageTokens(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    type: Literal['tokens']
    input_token_details: Optional[UsageTranscriptTextUsageTokensInputTokenDetails] = None

class UsageTranscriptTextUsageDuration(BaseModel):
    seconds: float
    type: Literal['duration']
Usage: TypeAlias = Union[UsageTranscriptTextUsageTokens, UsageTranscriptTextUsageDuration]

class Logprob(BaseModel):
    token: str
    bytes: List[int]
    logprob: float

class ConversationItemInputAudioTranscriptionCompletedEvent(BaseModel):
    content_index: int
    event_id: str
    item_id: str
    transcript: str
    type: Literal['conversation.item.input_audio_transcription.completed']
    usage: Usage
    logprobs: Optional[List[Logprob]] = None
