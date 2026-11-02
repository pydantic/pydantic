
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ....._models import BaseModel, UnionDiscriminator
from ..beta_plugin_target_rbac_group import BetaPluginTargetRBACGroup
from ..beta_plugin_target_organization import BetaPluginTargetOrganization
from ..beta_plugin_target_organization_member import BetaPluginTargetOrganizationMember
Target: TypeAlias = Annotated[Union[BetaPluginTargetOrganization, BetaPluginTargetRBACGroup, BetaPluginTargetOrganizationMember], UnionDiscriminator('type')]

class BetaPluginShare(BaseModel):
    """One share the owner of a member-owned Plugin has given.

    Shares are
    read-only in this API and have no ID of their own; who gave a share is
    recorded on the Compliance API activity feed, not here.
    """
    granted_at: datetime
    plugin_id: str
    target: Target
    type: Literal['plugin_share']
