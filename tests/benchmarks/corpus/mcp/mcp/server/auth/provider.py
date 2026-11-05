# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Any, Literal
from pydantic import AnyUrl, BaseModel

class AuthorizationParams(BaseModel):
    state: str | None
    scopes: list[str] | None
    code_challenge: str
    redirect_uri: AnyUrl
    redirect_uri_provided_explicitly: bool
    resource: str | None = None

class IdentityAssertionParams(BaseModel):
    assertion: str
    scopes: list[str] | None = None
    resource: str | None = None

class AuthorizationCode(BaseModel):
    code: str
    scopes: list[str]
    expires_at: float
    client_id: str
    code_challenge: str
    redirect_uri: AnyUrl
    redirect_uri_provided_explicitly: bool
    resource: str | None = None
    subject: str | None = None

class RefreshToken(BaseModel):
    token: str
    client_id: str
    scopes: list[str]
    expires_at: int | None = None
    resource: str | None = None
    subject: str | None = None

class AccessToken(BaseModel):
    token: str
    client_id: str
    scopes: list[str]
    expires_at: int | None = None
    resource: str | None = None
    subject: str | None = None
    claims: dict[str, Any] | None = None
RegistrationErrorCode = Literal['invalid_redirect_uri', 'invalid_client_metadata', 'invalid_software_statement', 'unapproved_software_statement']
AuthorizationErrorCode = Literal['invalid_request', 'unauthorized_client', 'access_denied', 'unsupported_response_type', 'invalid_scope', 'server_error', 'temporarily_unavailable', 'invalid_target']
TokenErrorCode = Literal['invalid_request', 'invalid_client', 'invalid_grant', 'unauthorized_client', 'unsupported_grant_type', 'invalid_scope', 'invalid_target']
