
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel

class CitationCharLocation(BaseModel):
    cited_text: str
    document_index: int
    document_title: Optional[str] = None
    end_char_index: int
    file_id: Optional[str] = None
    start_char_index: int
    type: Literal['char_location']
