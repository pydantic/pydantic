# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal
from ...._models import BaseModel

class Enforcement(BaseModel):
    """The current enforcement state of the hard spend limit."""
    status: Union[str, Literal['inactive', 'enforcing']]

class OrganizationSpendLimit(BaseModel):
    """Represents a hard spend limit configured at the organization level."""
    currency: Union[str, Literal['USD']]
    enforcement: Enforcement
    interval: Union[str, Literal['month']]
    object: Literal['organization.spend_limit']
    threshold_amount: int
