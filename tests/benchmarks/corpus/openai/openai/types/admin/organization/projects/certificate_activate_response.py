# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class CertificateDetails(BaseModel):
    expires_at: Optional[int] = None
    valid_at: Optional[int] = None

class CertificateActivateResponse(BaseModel):
    """Represents an individual certificate configured at the project level."""
    id: str
    active: bool
    certificate_details: CertificateDetails
    created_at: int
    name: Optional[str] = None
    object: Literal['organization.project.certificate']
