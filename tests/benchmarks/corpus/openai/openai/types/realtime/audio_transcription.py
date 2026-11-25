# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class AudioTranscription(BaseModel):
    delay: Optional[Literal['minimal', 'low', 'medium', 'high', 'xhigh']] = None
    keywords: Optional[List[str]] = None
    language: Optional[str] = None
    languages: Optional[List[str]] = None
    model: Union[str, Literal['whisper-1', 'gpt-transcribe', 'gpt-live-transcribe', 'gpt-4o-mini-transcribe', 'gpt-4o-mini-transcribe-2025-12-15', 'gpt-4o-transcribe', 'gpt-4o-transcribe-diarize', 'gpt-realtime-whisper'], None] = None
    prompt: Optional[str] = None
