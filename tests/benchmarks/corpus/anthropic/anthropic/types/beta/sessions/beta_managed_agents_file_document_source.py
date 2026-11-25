
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsFileDocumentSource(BaseModel):
    """Document referenced by file ID."""
    file_id: str
    type: Literal['file']
