
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class CacheMissModelChanged(BaseModel):
    """
    A `cache_miss_reason` for a request whose `model` or `speed` differs from the previous request's.

    See the [cache diagnostics guide](https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics#cache-miss-reason-types) to learn what to change for each reason.
    """
    cache_missed_input_tokens: int
    type: Literal['model_changed']
