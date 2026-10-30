# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ....._models import BaseModel
from .credential_auth import CredentialAuth

class Credential(BaseModel):
    """Metadata for a stored credential. Secret values are never returned."""
    id: str
    auth: CredentialAuth
    created_at: int
    metadata: Dict[str, str] = FieldInfo(default_factory=dict)
    name: str
    object: Literal['vault.credential']
    updated_at: int
    vault_id: str
