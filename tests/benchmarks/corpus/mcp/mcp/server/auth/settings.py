# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
import warnings
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self
from mcp.shared.exceptions import MCPDeprecationWarning

class ClientRegistrationOptions(BaseModel):
    enabled: bool = False
    client_secret_expiry_seconds: int | None = None
    valid_scopes: list[str] | None = None
    default_scopes: list[str] | None = None

class RevocationOptions(BaseModel):
    enabled: bool = False

class AuthSettings(BaseModel):
    model_config = ConfigDict(url_preserve_empty_path=True)
    issuer_url: AnyHttpUrl = Field(..., description='OAuth authorization server URL that issues tokens for this resource server.')
    service_documentation_url: AnyHttpUrl | None = None
    client_registration_options: ClientRegistrationOptions | None = None
    revocation_options: RevocationOptions | None = None
    required_scopes: list[str] | None = None
    identity_assertion_enabled: bool = Field(default=False, description='Advertise and accept the SEP-990 Identity Assertion Authorization Grant (the RFC 7523 jwt-bearer grant carrying an ID-JAG) at the token endpoint, for enterprise IdP flows. The provider must implement `exchange_identity_assertion`.')
    resource_server_url: AnyHttpUrl | None = Field(..., description='The URL of the MCP server to be used as the resource identifier and base route to look up OAuth Protected Resource Metadata.')
    validate_token_resource: bool | None = Field(default=None, description="Only accept tokens the token verifier reports as issued for `resource_server_url` (`AccessToken.resource`, the RFC 8707 resource indicator). Enable it when your authorization server binds tokens to the `resource` the client requested; set it to False when your token verifier checks the token's audience itself. With `resource_server_url` set, leaving it unset warns and behaves as False; 3.0 makes True the default there.")

    @model_validator(mode='after')
    def _check_validate_token_resource(self) -> Self:
        if self.validate_token_resource and self.resource_server_url is None:
            raise ValueError('validate_token_resource requires resource_server_url')
        if self.validate_token_resource is None and self.resource_server_url is not None:
            warnings.warn("`AuthSettings.validate_token_resource` is not set, so bearer tokens are not checked against `resource_server_url`; it will default to True in 3.0 when `resource_server_url` is set. Set it to True to have the server refuse tokens issued for another resource, or to False if your TokenVerifier validates the token's audience itself.", MCPDeprecationWarning, stacklevel=3)
        return self
