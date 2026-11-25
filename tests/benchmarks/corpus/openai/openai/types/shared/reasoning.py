# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .reasoning_effort import ReasoningEffort

class Reasoning(BaseModel):
    """
    Configuration options for
    [reasoning models](https://developers.openai.com/api/docs/guides/reasoning).
    """
    context: Optional[Literal['auto', 'current_turn', 'all_turns']] = None
    effort: Optional[ReasoningEffort] = None
    generate_summary: Optional[Literal['auto', 'concise', 'detailed']] = None
    mode: Union[str, Literal['standard', 'pro'], None] = None
    summary: Optional[Literal['auto', 'concise', 'detailed']] = None
