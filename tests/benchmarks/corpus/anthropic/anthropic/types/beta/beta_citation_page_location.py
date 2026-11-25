
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaCitationPageLocation(BaseModel):
    cited_text: str
    document_index: int
    document_title: Optional[str] = None
    end_page_number: int
    file_id: Optional[str] = None
    start_page_number: int
    type: Literal['page_location']
