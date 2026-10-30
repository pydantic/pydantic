# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Literal
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Field
from mcp.server.auth.provider import TokenErrorCode

class AuthorizationCodeRequest(BaseModel):
    grant_type: Literal['authorization_code']
    code: str = Field(..., description='The authorization code')
    redirect_uri: AnyUrl | None = Field(None, description='Must be the same as redirect URI provided in /authorize')
    client_id: str
    client_secret: str | None = None
    code_verifier: str = Field(..., description='PKCE code verifier')
    resource: str | None = Field(None, description='Resource indicator for the token')

class RefreshTokenRequest(BaseModel):
    grant_type: Literal['refresh_token']
    refresh_token: str = Field(..., description='The refresh token')
    scope: str | None = Field(None, description='Optional scope parameter')
    client_id: str
    client_secret: str | None = None
    resource: str | None = Field(None, description='Resource indicator for the token')

class JwtBearerRequest(BaseModel):
    grant_type: Literal['urn:ietf:params:oauth:grant-type:jwt-bearer']
    assertion: str = Field(..., description='The ID-JAG (a signed JWT) being presented as the grant')
    scope: str | None = Field(None, description='Optional scope parameter')
    client_id: str
    client_secret: str | None = None
    resource: str | None = Field(None, description='Resource indicator for the token')

class TokenErrorResponse(BaseModel):
    error: TokenErrorCode
    error_description: str | None = None
    error_uri: AnyHttpUrl | None = None
