# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Any
from pydantic import BaseModel, Field

class SignedJWTParameters(BaseModel):
    issuer: str = Field(description='Issuer for JWT assertions (typically client_id).')
    subject: str = Field(description='Subject identifier for JWT assertions (typically client_id).')
    signing_key: str = Field(description='Private key for JWT signing (PEM format).')
    signing_algorithm: str = Field(default='RS256', description='Algorithm for signing JWT assertions.')
    lifetime_seconds: int = Field(default=300, description='Lifetime of generated JWT in seconds.')
    additional_claims: dict[str, Any] | None = Field(default=None, description='Additional claims.')
