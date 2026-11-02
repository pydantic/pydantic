
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_reference_block import BetaToolReferenceBlock

class BetaToolSearchToolSearchResultBlock(BaseModel):
    tool_references: List[BetaToolReferenceBlock]
    type: Literal['tool_search_tool_search_result']
