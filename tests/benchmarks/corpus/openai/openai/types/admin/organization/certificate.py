# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class CertificateDetails(BaseModel):
    content: Optional[str] = None
    expires_at: Optional[int] = None
    valid_at: Optional[int] = None

class Certificate(BaseModel):
    """Represents an individual `certificate` uploaded to the organization."""
    id: str
    certificate_details: CertificateDetails
    created_at: int
    name: Optional[str] = None
    object: Literal['certificate', 'organization.certificate', 'organization.project.certificate']
    active: Optional[bool] = None
