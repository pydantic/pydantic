
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_document_block import BetaDocumentBlock

class BetaWebFetchBlock(BaseModel):
    content: BetaDocumentBlock
    retrieved_at: Optional[str] = None
    type: Literal['web_fetch_result']
    url: str
