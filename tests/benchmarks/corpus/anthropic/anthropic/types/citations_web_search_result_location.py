
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel

class CitationsWebSearchResultLocation(BaseModel):
    cited_text: str
    encrypted_index: str
    title: Optional[str] = None
    type: Literal['web_search_result_location']
    url: str
