
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ....._models import BaseModel, UnionDiscriminator
from ..beta_plugin_target_rbac_group import BetaPluginTargetRBACGroup
from ..beta_plugin_target_organization import BetaPluginTargetOrganization
from ..beta_plugin_target_organization_member import BetaPluginTargetOrganizationMember
Target: TypeAlias = Annotated[Union[BetaPluginTargetOrganization, BetaPluginTargetRBACGroup, BetaPluginTargetOrganizationMember], UnionDiscriminator('type')]

class BetaPluginInstallationSetting(BaseModel):
    """The installation setting an organization-owned Plugin holds for one
    target.

    It has no ID of its own: it is addressed by the Plugin's ID and the
    target.
    """
    created_at: datetime
    installation_preference: Literal['auto_install', 'available', 'not_available', 'required']
    plugin_id: str
    target: Target
    type: Literal['plugin_installation_setting']
    updated_at: datetime
