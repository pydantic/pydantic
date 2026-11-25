
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaContainerUploadBlock(BaseModel):
    """Response model for a file uploaded to the container."""
    file_id: str
    type: Literal['container_upload']
