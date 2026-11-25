# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class ActionSearchSource(BaseModel):
    """A source used in the search."""
    type: Literal['url']
    url: str

class ActionSearch(BaseModel):
    """Action type "search" - Performs a web search query."""
    type: Literal['search']
    queries: Optional[List[str]] = None
    query: Optional[str] = None
    sources: Optional[List[ActionSearchSource]] = None

class ActionOpenPage(BaseModel):
    """Action type "open_page" - Opens a specific URL from search results."""
    type: Literal['open_page']
    url: Optional[str] = None

class ActionFindInPage(BaseModel):
    """Action type "find_in_page": Searches for a pattern within a loaded page."""
    pattern: str
    type: Literal['find_in_page']
    url: str
Action: TypeAlias = Annotated[Union[ActionSearch, ActionOpenPage, ActionFindInPage], PropertyInfo(discriminator='type')]

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseFunctionWebSearch(BaseModel):
    """The results of a web search tool call.

    See the
    [web search guide](https://developers.openai.com/api/docs/guides/tools-web-search) for more information.
    """
    id: str
    action: Action
    status: Literal['in_progress', 'searching', 'completed', 'failed', 'incomplete']
    type: Literal['web_search_call']
    agent: Optional[Agent] = None
