
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from .._models import BaseModel
from .text_citation import TextCitation

class TextBlock(BaseModel):
    citations: Optional[List[TextCitation]] = None
    text: str
    type: Literal['text']
