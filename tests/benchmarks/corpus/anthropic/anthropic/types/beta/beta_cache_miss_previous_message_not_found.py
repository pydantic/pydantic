
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaCacheMissPreviousMessageNotFound(BaseModel):
    """
    A `cache_miss_reason` for when the API doesn't have a stored record of the request that `diagnostics.previous_message_id` references.

    This doesn't mean that this request changed.

    See the [cache diagnostics guide](https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics#cache-miss-reason-types) to learn what to change for each reason.
    """
    type: Literal['previous_message_not_found']
