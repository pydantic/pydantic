
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaCacheMissUnavailable(BaseModel):
    """A `cache_miss_reason` for when the API can't give a diagnosis.

    The request itself was processed normally.

    This includes a request whose `model`, `system`, and `tools` match the previous request's but whose other prompt-affecting parameters, such as `thinking` or `tool_choice`, differ.

    See the [cache diagnostics guide](https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics#cache-miss-reason-types) to learn what to change for each reason.
    """
    type: Literal['unavailable']
