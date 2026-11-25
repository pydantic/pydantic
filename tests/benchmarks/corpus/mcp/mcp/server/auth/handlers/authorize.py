# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Literal
from pydantic import AnyUrl, BaseModel, Field
from mcp.server.auth.provider import AuthorizationErrorCode

class AuthorizationRequest(BaseModel):
    client_id: str = Field(..., description='The client ID')
    redirect_uri: AnyUrl | None = Field(None, description='URL to redirect to after authorization')
    response_type: Literal['code'] = Field(..., description="Must be 'code' for authorization code flow")
    code_challenge: str = Field(..., description='PKCE code challenge')
    code_challenge_method: Literal['S256'] = Field('S256', description='PKCE code challenge method, must be S256')
    state: str | None = Field(None, description='Optional state parameter')
    scope: str | None = Field(None, description='Optional scope; if specified, should be a space-separated list of scope strings')
    resource: str | None = Field(None, description='RFC 8707 resource indicator - the MCP server this token will be used with')

class AuthorizationErrorResponse(BaseModel):
    error: AuthorizationErrorCode
    error_description: str | None
    error_uri: AnyUrl | None = None
    state: str | None = None
