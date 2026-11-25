
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_text_citation import BetaTextCitation

class BetaTextBlock(BaseModel):
    citations: Optional[List[BetaTextCitation]] = None
    text: str
    type: Literal['text']
