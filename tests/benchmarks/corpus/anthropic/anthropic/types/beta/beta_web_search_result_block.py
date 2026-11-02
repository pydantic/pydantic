
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebSearchResultBlock(BaseModel):
    encrypted_content: str
    page_age: Optional[str] = None
    title: str
    type: Literal['web_search_result']
    url: str
