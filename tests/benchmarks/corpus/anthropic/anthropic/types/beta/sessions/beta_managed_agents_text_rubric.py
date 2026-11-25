
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsTextRubric(BaseModel):
    """Rubric content provided inline as text."""
    content: str
    type: Literal['text']
