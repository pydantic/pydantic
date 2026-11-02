
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from .._models import BaseModel

class FileMetadata(BaseModel):
    id: str
    created_at: datetime
    filename: str
    mime_type: str
    size_bytes: int
    type: Literal['file']
    downloadable: Optional[bool] = None
    expires_at: Optional[datetime] = None
