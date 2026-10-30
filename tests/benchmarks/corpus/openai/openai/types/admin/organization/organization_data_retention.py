# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class OrganizationDataRetention(BaseModel):
    """Represents the organization's data retention control setting."""
    object: Literal['organization.data_retention']
    type: Literal['zero_data_retention', 'modified_abuse_monitoring', 'enhanced_zero_data_retention', 'enhanced_modified_abuse_monitoring']
