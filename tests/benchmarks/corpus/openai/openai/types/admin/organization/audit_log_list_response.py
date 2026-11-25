# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from ...._utils import PropertyInfo
from ...._models import BaseModel
from .aws_external_storage_provider import AwsExternalStorageProvider
from .gcp_external_storage_provider import GcpExternalStorageProvider
from .oci_external_storage_provider import OciExternalStorageProvider
from .azure_external_storage_provider import AzureExternalStorageProvider

class ActorAPIKeyServiceAccount(BaseModel):
    """The service account that performed the audit logged action."""
    id: Optional[str] = None

class ActorAPIKeyUser(BaseModel):
    """The user who performed the audit logged action."""
    id: Optional[str] = None
    email: Optional[str] = None

class ActorAPIKey(BaseModel):
    """The API Key used to perform the audit logged action."""
    id: Optional[str] = None
    service_account: Optional[ActorAPIKeyServiceAccount] = None
    type: Optional[Literal['user', 'service_account']] = None
    user: Optional[ActorAPIKeyUser] = None

class ActorSessionUser(BaseModel):
    """The user who performed the audit logged action."""
    id: Optional[str] = None
    email: Optional[str] = None

class ActorSession(BaseModel):
    """The session in which the audit logged action was performed."""
    ip_address: Optional[str] = None
    user: Optional[ActorSessionUser] = None

class Actor(BaseModel):
    """The actor who performed the audit logged action."""
    api_key: Optional[ActorAPIKey] = None
    session: Optional[ActorSession] = None
    type: Optional[Literal['session', 'api_key']] = None

class APIKeyCreatedData(BaseModel):
    """The payload used to create the API key."""
    scopes: Optional[List[str]] = None

class APIKeyCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[APIKeyCreatedData] = None

class APIKeyDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class APIKeyUpdatedChangesRequested(BaseModel):
    """The payload used to update the API key."""
    scopes: Optional[List[str]] = None

class APIKeyUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[APIKeyUpdatedChangesRequested] = None

class CertificateCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    name: Optional[str] = None

class CertificateDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    certificate: Optional[str] = None
    name: Optional[str] = None

class CertificateUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    name: Optional[str] = None

class CertificatesActivatedCertificate(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

class CertificatesActivated(BaseModel):
    """The details for events with this `type`."""
    certificates: Optional[List[CertificatesActivatedCertificate]] = None

class CertificatesDeactivatedCertificate(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

class CertificatesDeactivated(BaseModel):
    """The details for events with this `type`."""
    certificates: Optional[List[CertificatesDeactivatedCertificate]] = None

class CheckpointPermissionCreatedData(BaseModel):
    """The payload used to create the checkpoint permission."""
    fine_tuned_model_checkpoint: Optional[str] = None
    project_id: Optional[str] = None

class CheckpointPermissionCreated(BaseModel):
    """
    The project and fine-tuned model checkpoint that the checkpoint permission was created for.
    """
    id: Optional[str] = None
    data: Optional[CheckpointPermissionCreatedData] = None

class CheckpointPermissionDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class ExternalKeyRegistered(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[object] = None

class ExternalKeyRemoved(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
ExternalStorageRegisteredDataProvider: TypeAlias = Annotated[Union[AwsExternalStorageProvider, AzureExternalStorageProvider, GcpExternalStorageProvider, OciExternalStorageProvider], PropertyInfo(discriminator='type')]

class ExternalStorageRegisteredData(BaseModel):
    """The configuration for the external storage."""
    geography: Optional[str] = None
    provider: Optional[ExternalStorageRegisteredDataProvider] = None

class ExternalStorageRegistered(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[ExternalStorageRegisteredData] = None

class ExternalStorageRemoved(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class GroupCreatedData(BaseModel):
    """Information about the created group."""
    group_name: Optional[str] = None

class GroupCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[GroupCreatedData] = None

class GroupDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class GroupUpdatedChangesRequested(BaseModel):
    """The payload used to update the group."""
    group_name: Optional[str] = None

class GroupUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[GroupUpdatedChangesRequested] = None

class InviteAccepted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class InviteDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class InviteSentData(BaseModel):
    """The payload used to create the invite."""
    email: Optional[str] = None
    role: Optional[str] = None

class InviteSent(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[InviteSentData] = None

class IPAllowlistConfigActivatedConfig(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

class IPAllowlistConfigActivated(BaseModel):
    """The details for events with this `type`."""
    configs: Optional[List[IPAllowlistConfigActivatedConfig]] = None

class IPAllowlistConfigDeactivatedConfig(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

class IPAllowlistConfigDeactivated(BaseModel):
    """The details for events with this `type`."""
    configs: Optional[List[IPAllowlistConfigDeactivatedConfig]] = None

class IPAllowlistCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    name: Optional[str] = None

class IPAllowlistDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    name: Optional[str] = None

class IPAllowlistUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    allowed_ips: Optional[List[str]] = None

class LoginFailed(BaseModel):
    """The details for events with this `type`."""
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class LogoutFailed(BaseModel):
    """The details for events with this `type`."""
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class OrganizationUpdatedChangesRequested(BaseModel):
    """The payload used to update the organization settings."""
    api_call_logging: Optional[str] = None
    api_call_logging_project_ids: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    threads_ui_visibility: Optional[str] = None
    title: Optional[str] = None
    usage_dashboard_visibility: Optional[str] = None

class OrganizationUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[OrganizationUpdatedChangesRequested] = None

class Project(BaseModel):
    """The project that the action was scoped to.

    Absent for actions not scoped to projects. Note that any admin actions taken via Admin API keys are associated with the default project.
    """
    id: Optional[str] = None
    name: Optional[str] = None

class ProjectArchived(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class ProjectCreatedData(BaseModel):
    """The payload used to create the project."""
    name: Optional[str] = None
    title: Optional[str] = None

class ProjectCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[ProjectCreatedData] = None

class ProjectDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class ProjectUpdatedChangesRequested(BaseModel):
    """The payload used to update the project."""
    title: Optional[str] = None

class ProjectUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[ProjectUpdatedChangesRequested] = None

class RateLimitDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class RateLimitUpdatedChangesRequested(BaseModel):
    """The payload used to update the rate limits."""
    batch_1_day_max_input_tokens: Optional[int] = None
    max_audio_megabytes_per_1_minute: Optional[int] = None
    max_images_per_1_minute: Optional[int] = None
    max_requests_per_1_day: Optional[int] = None
    max_requests_per_1_minute: Optional[int] = None
    max_tokens_per_1_minute: Optional[int] = None

class RateLimitUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[RateLimitUpdatedChangesRequested] = None

class RoleAssignmentCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    principal_id: Optional[str] = None
    principal_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None

class RoleAssignmentDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    principal_id: Optional[str] = None
    principal_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None

class RoleBoundToResource(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    connector_id: Optional[str] = None
    connector_name: Optional[str] = None
    enabled: Optional[bool] = None
    permissions: Optional[List[str]] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    role_id: Optional[str] = None
    source: Optional[Literal['role_toggle', 'role_connector_update', 'role_delete', 'workspace_permissions', 'connector_publish']] = None
    workspace_id: Optional[str] = None

class RoleCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    permissions: Optional[List[str]] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    role_name: Optional[str] = None

class RoleDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class RoleUnboundFromResource(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    connector_id: Optional[str] = None
    connector_name: Optional[str] = None
    enabled: Optional[bool] = None
    permissions: Optional[List[str]] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    role_id: Optional[str] = None
    source: Optional[Literal['role_toggle', 'role_connector_update', 'role_delete', 'workspace_permissions', 'connector_publish']] = None
    workspace_id: Optional[str] = None

class RoleUpdatedChangesRequested(BaseModel):
    """The payload used to update the role."""
    description: Optional[str] = None
    metadata: Optional[object] = None
    permissions_added: Optional[List[str]] = None
    permissions_removed: Optional[List[str]] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    role_name: Optional[str] = None

class RoleUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[RoleUpdatedChangesRequested] = None

class ScimDisabled(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class ScimEnabled(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class ServiceAccountCreatedData(BaseModel):
    """The payload used to create the service account."""
    role: Optional[str] = None

class ServiceAccountCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[ServiceAccountCreatedData] = None

class ServiceAccountDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class ServiceAccountUpdatedChangesRequested(BaseModel):
    """The payload used to updated the service account."""
    role: Optional[str] = None

class ServiceAccountUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[ServiceAccountUpdatedChangesRequested] = None

class UserAddedData(BaseModel):
    """The payload used to add the user to the project."""
    role: Optional[str] = None

class UserAdded(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[UserAddedData] = None

class UserDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None

class UserUpdatedChangesRequested(BaseModel):
    """The payload used to update the user."""
    role: Optional[str] = None

class UserUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[UserUpdatedChangesRequested] = None

class WorkloadIdentityProviderMappingCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[object] = None
    identity_provider_id: Optional[str] = None

class WorkloadIdentityProviderMappingDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    identity_provider_id: Optional[str] = None
    project_id: Optional[str] = None
    service_account_id: Optional[str] = None

class WorkloadIdentityProviderMappingUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[object] = None
    identity_provider_id: Optional[str] = None

class WorkloadIdentityProviderCreated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    data: Optional[object] = None

class WorkloadIdentityProviderDeleted(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    name: Optional[str] = None

class WorkloadIdentityProviderUpdated(BaseModel):
    """The details for events with this `type`."""
    id: Optional[str] = None
    changes_requested: Optional[object] = None

class AuditLogListResponse(BaseModel):
    """A log of a user action or configuration change within this organization."""
    id: str
    effective_at: int
    type: Literal['api_key.created', 'api_key.updated', 'api_key.deleted', 'certificate.created', 'certificate.updated', 'certificate.deleted', 'certificates.activated', 'certificates.deactivated', 'checkpoint.permission.created', 'checkpoint.permission.deleted', 'external_key.registered', 'external_key.removed', 'external_storage.registered', 'external_storage.removed', 'group.created', 'group.updated', 'group.deleted', 'invite.sent', 'invite.accepted', 'invite.deleted', 'ip_allowlist.created', 'ip_allowlist.updated', 'ip_allowlist.deleted', 'ip_allowlist.config.activated', 'ip_allowlist.config.deactivated', 'login.succeeded', 'login.failed', 'logout.succeeded', 'logout.failed', 'organization.updated', 'project.created', 'project.updated', 'project.archived', 'project.deleted', 'rate_limit.updated', 'rate_limit.deleted', 'resource.deleted', 'tunnel.created', 'tunnel.updated', 'tunnel.deleted', 'workload_identity_provider.created', 'workload_identity_provider.updated', 'workload_identity_provider.deleted', 'workload_identity_provider_mapping.created', 'workload_identity_provider_mapping.updated', 'workload_identity_provider_mapping.deleted', 'role.created', 'role.updated', 'role.deleted', 'role.assignment.created', 'role.assignment.deleted', 'role.bound_to_resource', 'role.unbound_from_resource', 'scim.enabled', 'scim.disabled', 'service_account.created', 'service_account.updated', 'service_account.deleted', 'user.added', 'user.updated', 'user.deleted', 'tenant.metadata.updated', 'tenant.microsoft_entra_mapping.upserted', 'tenant.microsoft_entra_mapping.deleted', 'tenant.workload_identity.provider.created', 'tenant.workload_identity.provider.updated', 'tenant.workload_identity.provider.archived', 'tenant.workload_identity.mapping.created', 'tenant.workload_identity.mapping.updated', 'tenant.workload_identity.mapping.archived', 'tenant.workload_identity.binding.created', 'tenant.workload_identity.principal.provisioned', 'tenant.workload_identity.access_token.issued', 'tenant.admin_api_key.created', 'tenant.admin_api_key.updated', 'tenant.admin_api_key.deleted', 'tenant.project_api_key.created', 'tenant.trusted_access.business_verification.started', 'tenant.trusted_access.application.submitted', 'tenant.chatgpt_access_token.revoked', 'tenant.migration.completed', 'tenant.sso.migrated', 'tenant.domains.migrated', 'tenant.sso_connection.created', 'tenant.sso_connection.updated', 'tenant.sso_connection.deleted', 'tenant.sso_connection.setup.started', 'tenant.policy.created', 'tenant.policy.updated', 'tenant.policy.deleted', 'tenant.policy.attached', 'tenant.policy.detached', 'tenant.principal_authentication_policy.resolved', 'tenant.scim.setup.started', 'tenant.scim.deletion.requested', 'tenant.scim.directory.created', 'tenant.product_access_policy.updated', 'tenant.resource_share_grant.created', 'tenant.resource_share_grant.updated', 'tenant.resource_share_grant.accepted', 'tenant.resource_share_grant.declined', 'tenant.resource_share_grant.revoked', 'tenant.resource_share_grant.deleted', 'tenant.service_account.updated', 'tenant.service_account.deleted', 'tenant.service_account.token.revoked', 'tenant.billing.overage_limit.updated', 'tenant.billing.alerts.updated', 'tenant.billing.info.updated', 'tenant.usage_limit.workspace.updated', 'tenant.usage_limit.group.updated', 'tenant.usage_limit.user.updated', 'tenant.usage_limit.increase_request.updated', 'tenant.usage_limit.increase_request.resolved', 'tenant.group.created', 'tenant.group.updated', 'tenant.group.deleted', 'tenant.group.member.added', 'tenant.group.member.removed', 'tenant.migration_rollout.status.updated', 'tenant.migration_rollout.tier.updated', 'tenant.role.metadata.updated', 'tenant.custom_role.created', 'tenant.custom_role.updated', 'tenant.custom_role.deleted', 'tenant.role_assignment.created', 'tenant.role_assignment.deleted', 'tenant.resource_role_assignment.created', 'tenant.resource_role_assignment.deleted', 'tenant.resource_access.updated', 'tenant.resource_access.deleted', 'tenant.ads_account.onboarding.redemption', 'tenant.session_policy.created', 'tenant.session_policy.updated', 'tenant.session_policy.deleted', 'tenant.session_revocation.started', 'tenant.third_party_app_policy.updated', 'tenant.user.added', 'tenant.user.updated', 'tenant.user.removed', 'tenant.user.looked_up', 'tenant.user.invited', 'tenant.membership.revoked', 'tenant.api_organization_invite.upserted', 'tenant.api_organization_invite.deleted', 'tenant.chatgpt_workspace_invite.upserted', 'tenant.membership.accepted', 'tenant.membership.declined', 'tenant.workspace_invite_email_settings.updated']
    actor: Optional[Actor] = None
    api_key_created: Optional[APIKeyCreated] = FieldInfo(alias='api_key.created', default=None)
    api_key_deleted: Optional[APIKeyDeleted] = FieldInfo(alias='api_key.deleted', default=None)
    api_key_updated: Optional[APIKeyUpdated] = FieldInfo(alias='api_key.updated', default=None)
    certificate_created: Optional[CertificateCreated] = FieldInfo(alias='certificate.created', default=None)
    certificate_deleted: Optional[CertificateDeleted] = FieldInfo(alias='certificate.deleted', default=None)
    certificate_updated: Optional[CertificateUpdated] = FieldInfo(alias='certificate.updated', default=None)
    certificates_activated: Optional[CertificatesActivated] = FieldInfo(alias='certificates.activated', default=None)
    certificates_deactivated: Optional[CertificatesDeactivated] = FieldInfo(alias='certificates.deactivated', default=None)
    checkpoint_permission_created: Optional[CheckpointPermissionCreated] = FieldInfo(alias='checkpoint.permission.created', default=None)
    checkpoint_permission_deleted: Optional[CheckpointPermissionDeleted] = FieldInfo(alias='checkpoint.permission.deleted', default=None)
    external_key_registered: Optional[ExternalKeyRegistered] = FieldInfo(alias='external_key.registered', default=None)
    external_key_removed: Optional[ExternalKeyRemoved] = FieldInfo(alias='external_key.removed', default=None)
    external_storage_registered: Optional[ExternalStorageRegistered] = FieldInfo(alias='external_storage.registered', default=None)
    external_storage_removed: Optional[ExternalStorageRemoved] = FieldInfo(alias='external_storage.removed', default=None)
    group_created: Optional[GroupCreated] = FieldInfo(alias='group.created', default=None)
    group_deleted: Optional[GroupDeleted] = FieldInfo(alias='group.deleted', default=None)
    group_updated: Optional[GroupUpdated] = FieldInfo(alias='group.updated', default=None)
    invite_accepted: Optional[InviteAccepted] = FieldInfo(alias='invite.accepted', default=None)
    invite_deleted: Optional[InviteDeleted] = FieldInfo(alias='invite.deleted', default=None)
    invite_sent: Optional[InviteSent] = FieldInfo(alias='invite.sent', default=None)
    ip_allowlist_config_activated: Optional[IPAllowlistConfigActivated] = FieldInfo(alias='ip_allowlist.config.activated', default=None)
    ip_allowlist_config_deactivated: Optional[IPAllowlistConfigDeactivated] = FieldInfo(alias='ip_allowlist.config.deactivated', default=None)
    ip_allowlist_created: Optional[IPAllowlistCreated] = FieldInfo(alias='ip_allowlist.created', default=None)
    ip_allowlist_deleted: Optional[IPAllowlistDeleted] = FieldInfo(alias='ip_allowlist.deleted', default=None)
    ip_allowlist_updated: Optional[IPAllowlistUpdated] = FieldInfo(alias='ip_allowlist.updated', default=None)
    login_failed: Optional[LoginFailed] = FieldInfo(alias='login.failed', default=None)
    login_succeeded: Optional[object] = FieldInfo(alias='login.succeeded', default=None)
    logout_failed: Optional[LogoutFailed] = FieldInfo(alias='logout.failed', default=None)
    logout_succeeded: Optional[object] = FieldInfo(alias='logout.succeeded', default=None)
    organization_updated: Optional[OrganizationUpdated] = FieldInfo(alias='organization.updated', default=None)
    project: Optional[Project] = None
    project_archived: Optional[ProjectArchived] = FieldInfo(alias='project.archived', default=None)
    project_created: Optional[ProjectCreated] = FieldInfo(alias='project.created', default=None)
    project_deleted: Optional[ProjectDeleted] = FieldInfo(alias='project.deleted', default=None)
    project_updated: Optional[ProjectUpdated] = FieldInfo(alias='project.updated', default=None)
    rate_limit_deleted: Optional[RateLimitDeleted] = FieldInfo(alias='rate_limit.deleted', default=None)
    rate_limit_updated: Optional[RateLimitUpdated] = FieldInfo(alias='rate_limit.updated', default=None)
    role_assignment_created: Optional[RoleAssignmentCreated] = FieldInfo(alias='role.assignment.created', default=None)
    role_assignment_deleted: Optional[RoleAssignmentDeleted] = FieldInfo(alias='role.assignment.deleted', default=None)
    role_bound_to_resource: Optional[RoleBoundToResource] = FieldInfo(alias='role.bound_to_resource', default=None)
    role_created: Optional[RoleCreated] = FieldInfo(alias='role.created', default=None)
    role_deleted: Optional[RoleDeleted] = FieldInfo(alias='role.deleted', default=None)
    role_unbound_from_resource: Optional[RoleUnboundFromResource] = FieldInfo(alias='role.unbound_from_resource', default=None)
    role_updated: Optional[RoleUpdated] = FieldInfo(alias='role.updated', default=None)
    scim_disabled: Optional[ScimDisabled] = FieldInfo(alias='scim.disabled', default=None)
    scim_enabled: Optional[ScimEnabled] = FieldInfo(alias='scim.enabled', default=None)
    service_account_created: Optional[ServiceAccountCreated] = FieldInfo(alias='service_account.created', default=None)
    service_account_deleted: Optional[ServiceAccountDeleted] = FieldInfo(alias='service_account.deleted', default=None)
    service_account_updated: Optional[ServiceAccountUpdated] = FieldInfo(alias='service_account.updated', default=None)
    user_added: Optional[UserAdded] = FieldInfo(alias='user.added', default=None)
    user_deleted: Optional[UserDeleted] = FieldInfo(alias='user.deleted', default=None)
    user_updated: Optional[UserUpdated] = FieldInfo(alias='user.updated', default=None)
    workload_identity_provider_mapping_created: Optional[WorkloadIdentityProviderMappingCreated] = FieldInfo(alias='workload_identity_provider_mapping.created', default=None)
    workload_identity_provider_mapping_deleted: Optional[WorkloadIdentityProviderMappingDeleted] = FieldInfo(alias='workload_identity_provider_mapping.deleted', default=None)
    workload_identity_provider_mapping_updated: Optional[WorkloadIdentityProviderMappingUpdated] = FieldInfo(alias='workload_identity_provider_mapping.updated', default=None)
    workload_identity_provider_created: Optional[WorkloadIdentityProviderCreated] = FieldInfo(alias='workload_identity_provider.created', default=None)
    workload_identity_provider_deleted: Optional[WorkloadIdentityProviderDeleted] = FieldInfo(alias='workload_identity_provider.deleted', default=None)
    workload_identity_provider_updated: Optional[WorkloadIdentityProviderUpdated] = FieldInfo(alias='workload_identity_provider.updated', default=None)
