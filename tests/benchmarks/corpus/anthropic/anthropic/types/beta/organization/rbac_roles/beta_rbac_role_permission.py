
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ....._models import BaseModel, UnionDiscriminator
from .beta_rbac_connector_permission_resource import BetaRBACConnectorPermissionResource
from .beta_rbac_organization_permission_resource import BetaRBACOrganizationPermissionResource
from .beta_rbac_all_connectors_permission_resource import BetaRBACAllConnectorsPermissionResource
from .beta_rbac_connector_tool_permission_resource import BetaRBACConnectorToolPermissionResource
from .beta_rbac_connector_scope_permission_resource import BetaRBACConnectorScopePermissionResource
Resource: TypeAlias = Annotated[Union[BetaRBACOrganizationPermissionResource, BetaRBACConnectorToolPermissionResource, BetaRBACConnectorScopePermissionResource, BetaRBACConnectorPermissionResource, BetaRBACAllConnectorsPermissionResource], UnionDiscriminator('type')]

class BetaRBACRolePermission(BaseModel):
    action: str
    resource: Resource
    type: Literal['rbac_role_permission']
