
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsMemoryPrefix(BaseModel):
    """
    A directory marker that [List Memories](https://platform.claude.com/docs/en/api/beta/memory_stores/memories/list) returns instead of the memories below the requested `depth`.

    It stands for one or more memories whose paths start with `path`. It isn't a stored object and doesn't have an ID. Each marker counts toward the page `limit`.
    """
    path: str
    type: Literal['memory_prefix']
