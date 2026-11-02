# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .log_prob_properties import LogProbProperties
from ..audio.transcription_language import TranscriptionLanguage

class UsageTranscriptTextUsageTokensInputTokenDetails(BaseModel):
    """Details about the input tokens billed for this request."""
    audio_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class UsageTranscriptTextUsageTokens(BaseModel):
    """Usage statistics for models billed by token usage."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    type: Literal['tokens']
    input_token_details: Optional[UsageTranscriptTextUsageTokensInputTokenDetails] = None

class UsageTranscriptTextUsageDuration(BaseModel):
    """Usage statistics for models billed by audio input duration."""
    seconds: float
    type: Literal['duration']
Usage: TypeAlias = Union[UsageTranscriptTextUsageTokens, UsageTranscriptTextUsageDuration]

class ConversationItemInputAudioTranscriptionCompletedEvent(BaseModel):
    """
    This event is the output of audio transcription for user audio written to the
    user audio buffer. Transcription begins when the input audio buffer is
    committed by the client or server (when VAD is enabled). Transcription runs
    asynchronously with Response creation, so this event may come before or after
    the Response events.

    Realtime API models accept audio natively, and thus input transcription is a
    separate process run on a separate ASR (Automatic Speech Recognition) model.
    The transcript may diverge somewhat from the model's interpretation, and
    should be treated as a rough guide.
    """
    content_index: int
    event_id: str
    item_id: str
    transcript: str
    type: Literal['conversation.item.input_audio_transcription.completed']
    usage: Usage
    languages: Optional[List[TranscriptionLanguage]] = None
    logprobs: Optional[List[LogProbProperties]] = None
