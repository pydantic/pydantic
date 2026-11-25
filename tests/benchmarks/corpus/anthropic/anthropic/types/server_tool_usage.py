
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel

class ServerToolUsage(BaseModel):
    web_fetch_requests: int
    web_search_requests: int
