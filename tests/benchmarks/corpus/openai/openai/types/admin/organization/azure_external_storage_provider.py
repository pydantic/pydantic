# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class AzureExternalStorageProvider(BaseModel):
    account_name: str
    container: str
    region: str
    resource_group: str
    subscription_id: str
    tenant_id: str
    type: Literal['azure']
