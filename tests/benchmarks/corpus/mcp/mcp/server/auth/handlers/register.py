# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from pydantic import BaseModel
from mcp.server.auth.provider import RegistrationErrorCode

class RegistrationErrorResponse(BaseModel):
    error: RegistrationErrorCode
    error_description: str | None
