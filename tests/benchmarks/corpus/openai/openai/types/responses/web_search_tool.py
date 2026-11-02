# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Filters(BaseModel):
    """Filters for the search."""
    allowed_domains: Optional[List[str]] = None

class UserLocation(BaseModel):
    """The approximate location of the user.

    If omitted or null, defaults to the
    United States. To avoid this fallback, pass `{"type": "approximate"}` without
    location fields. To localize results, provide the relevant location fields.
    """
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    timezone: Optional[str] = None
    type: Optional[Literal['approximate']] = None

class WebSearchTool(BaseModel):
    """Search the Internet for sources related to the prompt.

    Learn more about the
    [web search tool](https://developers.openai.com/api/docs/guides/tools-web-search).
    """
    type: Literal['web_search', 'web_search_2025_08_26']
    external_web_access: Optional[bool] = None
    filters: Optional[Filters] = None
    search_context_size: Optional[Literal['low', 'medium', 'high']] = None
    user_location: Optional[UserLocation] = None
