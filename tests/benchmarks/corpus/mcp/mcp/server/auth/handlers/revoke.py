# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Literal
from pydantic import BaseModel

class RevocationRequest(BaseModel):
    token: str
    token_type_hint: Literal['access_token', 'refresh_token'] | None = None
    client_id: str
    client_secret: str | None

class RevocationErrorResponse(BaseModel):
    error: Literal['invalid_request', 'unauthorized_client']
    error_description: str | None = None
