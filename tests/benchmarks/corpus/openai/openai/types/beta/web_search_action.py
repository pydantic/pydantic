# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class WebSearchActionResourceSearch(BaseModel):
    """A search query or group of search queries."""
    queries: Optional[List[str]] = None
    query: Optional[str] = None
    type: Literal['search']

class WebSearchActionResourceOpenPage(BaseModel):
    """Opens a web page."""
    type: Literal['open_page']
    url: Optional[str] = None

class WebSearchActionResourceFindInPage(BaseModel):
    """Finds text within a web page."""
    pattern: Optional[str] = None
    type: Literal['find_in_page']
    url: Optional[str] = None

class WebSearchActionResourceOther(BaseModel):
    """Another web search action."""
    type: Literal['other']
WebSearchAction: TypeAlias = Annotated[Union[WebSearchActionResourceSearch, WebSearchActionResourceOpenPage, WebSearchActionResourceFindInPage, WebSearchActionResourceOther], PropertyInfo(discriminator='type')]
