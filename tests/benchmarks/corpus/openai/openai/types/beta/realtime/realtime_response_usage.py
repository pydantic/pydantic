
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class InputTokenDetails(BaseModel):
    audio_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class OutputTokenDetails(BaseModel):
    audio_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class RealtimeResponseUsage(BaseModel):
    input_token_details: Optional[InputTokenDetails] = None
    input_tokens: Optional[int] = None
    output_token_details: Optional[OutputTokenDetails] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
