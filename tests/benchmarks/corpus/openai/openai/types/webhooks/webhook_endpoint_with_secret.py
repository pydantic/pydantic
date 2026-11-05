# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ..._models import BaseModel

class WebhookEndpointWithSecret(BaseModel):
    id: str
    created_at: int
    event_types: List[str]
    name: str
    object: Literal['webhook_endpoint']
    signing_secret: str = FieldInfo(repr=False)
    signing_secret_hint: Optional[str] = None
    url: str
    updated_at: Optional[int] = None
