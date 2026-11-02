
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaDreamUsage(BaseModel):
    """The tokens that a dream has used so far.

    The counts are zero while the dream is `pending` and update while it is `running`. They can keep changing after a cancel.

    See the [Dreams guide](https://platform.claude.com/docs/en/managed-agents/dreams#billing) for how dreams are billed. See the [prompt caching guide](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#tracking-cache-performance) for how the input token counts add up.
    """
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    input_tokens: int
    output_tokens: int
