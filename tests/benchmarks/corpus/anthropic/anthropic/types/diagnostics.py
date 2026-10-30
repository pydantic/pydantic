
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .cache_miss_reason import CacheMissReason

class Diagnostics(BaseModel):
    """
    Request-level diagnostics: why the prompt cache could not fully reuse
    the prefix of the request named by `diagnostics.previous_message_id`.
    """
    cache_miss_reason: Optional[CacheMissReason] = None
