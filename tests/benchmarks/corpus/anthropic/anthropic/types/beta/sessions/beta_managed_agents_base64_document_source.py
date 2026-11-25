
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsBase64DocumentSource(BaseModel):
    """Base64-encoded document data."""
    data: str
    media_type: str
    type: Literal['base64']
