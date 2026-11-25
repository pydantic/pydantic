# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .realtime_response_usage_input_token_details import RealtimeResponseUsageInputTokenDetails
from .realtime_response_usage_output_token_details import RealtimeResponseUsageOutputTokenDetails

class RealtimeResponseUsage(BaseModel):
    """Usage statistics for the Response, this will correspond to billing.

    A
    Realtime API session will maintain a conversation context and append new
    Items to the Conversation, thus output from previous turns (text and
    audio tokens) will become the input for later turns.
    """
    input_token_details: Optional[RealtimeResponseUsageInputTokenDetails] = None
    input_tokens: Optional[int] = None
    output_token_details: Optional[RealtimeResponseUsageOutputTokenDetails] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
