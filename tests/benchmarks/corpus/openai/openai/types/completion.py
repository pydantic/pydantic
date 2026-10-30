# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from .._models import BaseModel
from .completion_usage import CompletionUsage
from .completion_choice import CompletionChoice

class Completion(BaseModel):
    """Represents a completion response from the API.

    Note: both the streamed and non-streamed response objects share the same shape (unlike the chat endpoint).
    """
    id: str
    choices: List[CompletionChoice]
    created: int
    model: str
    object: Literal['text_completion']
    system_fingerprint: Optional[str] = None
    usage: Optional[CompletionUsage] = None
