
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .document_block import DocumentBlock

class WebFetchBlock(BaseModel):
    content: DocumentBlock
    retrieved_at: Optional[str] = None
    type: Literal['web_fetch_result']
    url: str
