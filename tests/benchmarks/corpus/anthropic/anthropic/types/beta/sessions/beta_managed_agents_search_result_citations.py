
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaManagedAgentsSearchResultCitations(BaseModel):
    """Citation settings for a search result."""
    enabled: bool
