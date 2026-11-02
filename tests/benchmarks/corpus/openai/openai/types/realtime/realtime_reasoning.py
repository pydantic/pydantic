# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .realtime_reasoning_effort import RealtimeReasoningEffort

class RealtimeReasoning(BaseModel):
    """Configuration for reasoning-capable Realtime models such as `gpt-realtime-2`."""
    effort: Optional[RealtimeReasoningEffort] = None
