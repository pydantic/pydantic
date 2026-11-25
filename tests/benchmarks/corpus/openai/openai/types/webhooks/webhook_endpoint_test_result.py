# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class WebhookEndpointTestResult(BaseModel):
    event_type: str
    object: Literal['webhook_endpoint.test']
    status_code: int
    success: Literal[True]
    webhook_endpoint_id: str
