
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_search_result_content import BetaManagedAgentsSearchResultContent
from .beta_managed_agents_search_result_citations import BetaManagedAgentsSearchResultCitations

class BetaManagedAgentsSearchResultBlock(BaseModel):
    """A block containing a web search result."""
    citations: BetaManagedAgentsSearchResultCitations
    content: List[BetaManagedAgentsSearchResultContent]
    source: str
    title: str
    type: Literal['search_result']
