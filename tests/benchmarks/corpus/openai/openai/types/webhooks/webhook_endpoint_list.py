# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .webhook_endpoint import WebhookEndpoint

class WebhookEndpointList(BaseModel):
    data: List[WebhookEndpoint]
    first_id: Optional[str] = None
    has_more: bool
    last_id: Optional[str] = None
    object: Literal['list']
