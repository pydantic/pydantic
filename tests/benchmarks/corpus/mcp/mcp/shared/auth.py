# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Any, Literal, cast
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, ConfigDict, Field, field_validator, model_validator
TokenEndpointAuthMethod = Literal['none', 'client_secret_post', 'client_secret_basic', 'private_key_jwt']
DEFAULT_GRANT_TYPES = ['authorization_code', 'refresh_token']

def _empty_str_to_none(v: object) -> object:
    if v == '':
        return None
    return v

class OAuthToken(BaseModel):
    access_token: str
    token_type: Literal['Bearer'] = 'Bearer'
    expires_in: int | None = None
    scope: str | None = None
    refresh_token: str | None = None

    @field_validator('token_type', mode='before')
    @classmethod
    def normalize_token_type(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.title()
        return v

class AuthorizationCodeResult(BaseModel):
    code: str
    state: str | None = None
    iss: str | None = None

class OAuthClientMetadataBase(BaseModel):
    model_config = ConfigDict(url_preserve_empty_path=True)
    response_types: list[str] = ['code']
    scope: str | None = None
    client_name: str | None = None
    client_uri: AnyHttpUrl | None = None
    logo_uri: AnyHttpUrl | None = None
    contacts: list[str] | None = None
    tos_uri: AnyHttpUrl | None = None
    policy_uri: AnyHttpUrl | None = None
    jwks_uri: AnyHttpUrl | None = None
    jwks: Any | None = None
    software_id: str | None = None
    software_version: str | None = None

    @field_validator('client_uri', 'logo_uri', 'tos_uri', 'policy_uri', 'jwks_uri', mode='before')
    @classmethod
    def _empty_string_optional_url_to_none(cls, v: object) -> object:
        return _empty_str_to_none(v)

class OAuthClientMetadata(OAuthClientMetadataBase):
    redirect_uris: list[AnyUrl] | None = Field(..., min_length=1)
    token_endpoint_auth_method: TokenEndpointAuthMethod | None = None
    grant_types: list[Literal['authorization_code', 'refresh_token', 'urn:ietf:params:oauth:grant-type:jwt-bearer'] | str] = list(DEFAULT_GRANT_TYPES)
    application_type: Literal['web', 'native'] = 'native'

class OAuthClientInformationFull(OAuthClientMetadataBase):
    redirect_uris: list[AnyUrl] | None = None
    token_endpoint_auth_method: str | None = None
    grant_types: list[str] = list(DEFAULT_GRANT_TYPES)
    application_type: str | None = None
    client_id: str
    client_secret: str | None = None
    client_id_issued_at: int | None = None
    client_secret_expires_at: int | None = None
    issuer: str | None = None

    @model_validator(mode='before')
    @classmethod
    def _placeholder_members_read_as_omitted(cls, data: object) -> object:
        if isinstance(data, dict):
            members = cast(dict[str, Any], data)
            return {key: value for key, value in members.items() if value is not None and value != ''}
        return data

class OAuthMetadata(BaseModel):
    model_config = ConfigDict(url_preserve_empty_path=True)
    issuer: AnyHttpUrl
    authorization_endpoint: AnyHttpUrl
    token_endpoint: AnyHttpUrl
    registration_endpoint: AnyHttpUrl | None = None
    scopes_supported: list[str] | None = None
    response_types_supported: list[str] = ['code']
    response_modes_supported: list[str] | None = None
    grant_types_supported: list[str] | None = None
    token_endpoint_auth_methods_supported: list[str] | None = None
    token_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    service_documentation: AnyHttpUrl | None = None
    ui_locales_supported: list[str] | None = None
    op_policy_uri: AnyHttpUrl | None = None
    op_tos_uri: AnyHttpUrl | None = None
    revocation_endpoint: AnyHttpUrl | None = None
    revocation_endpoint_auth_methods_supported: list[str] | None = None
    revocation_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    introspection_endpoint: AnyHttpUrl | None = None
    introspection_endpoint_auth_methods_supported: list[str] | None = None
    introspection_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    code_challenge_methods_supported: list[str] | None = None
    client_id_metadata_document_supported: bool | None = None
    authorization_response_iss_parameter_supported: bool | None = None
    authorization_grant_profiles_supported: list[str] | None = None

class ProtectedResourceMetadata(BaseModel):
    model_config = ConfigDict(url_preserve_empty_path=True)
    resource: AnyHttpUrl
    authorization_servers: list[AnyHttpUrl] = Field(..., min_length=1)
    jwks_uri: AnyHttpUrl | None = None
    scopes_supported: list[str] | None = None
    bearer_methods_supported: list[str] | None = Field(default=['header'])
    resource_signing_alg_values_supported: list[str] | None = None
    resource_name: str | None = None
    resource_documentation: AnyHttpUrl | None = None
    resource_policy_uri: AnyHttpUrl | None = None
    resource_tos_uri: AnyHttpUrl | None = None
    tls_client_certificate_bound_access_tokens: bool | None = None
    authorization_details_types_supported: list[str] | None = None
    dpop_signing_alg_values_supported: list[str] | None = None
    dpop_bound_access_tokens_required: bool | None = None
