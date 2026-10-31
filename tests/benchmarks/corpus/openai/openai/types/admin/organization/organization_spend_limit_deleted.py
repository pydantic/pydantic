# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class OrganizationSpendLimitDeleted(BaseModel):
    """Confirmation payload returned after deleting an organization hard spend limit."""
    deleted: bool
    object: Literal['organization.spend_limit.deleted']
