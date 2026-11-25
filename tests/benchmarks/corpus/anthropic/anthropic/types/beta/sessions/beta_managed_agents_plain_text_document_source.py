
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsPlainTextDocumentSource(BaseModel):
    """Plain text document content."""
    data: str
    media_type: Literal['text/plain']
    type: Literal['text']
