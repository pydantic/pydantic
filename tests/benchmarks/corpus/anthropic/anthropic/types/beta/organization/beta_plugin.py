
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_plugin_api_actor import BetaPluginAPIActor
from .beta_plugin_component import BetaPluginComponent
from .beta_plugin_owner_user import BetaPluginOwnerUser
from .beta_plugin_user_actor import BetaPluginUserActor
from .beta_plugin_content_scan import BetaPluginContentScan
from .beta_plugin_owner_organization import BetaPluginOwnerOrganization
CreatedBy: TypeAlias = Annotated[Union[BetaPluginUserActor, BetaPluginAPIActor, None], UnionDiscriminator('type')]
Owner: TypeAlias = Annotated[Union[BetaPluginOwnerOrganization, BetaPluginOwnerUser], UnionDiscriminator('type')]

class BetaPlugin(BaseModel):
    id: str
    components: Optional[List[BetaPluginComponent]] = None
    content_scan: Optional[BetaPluginContentScan] = None
    created_at: datetime
    created_by: Optional[CreatedBy] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    latest_version_id: str
    manifest_version: Optional[str] = None
    marketplace_id: str
    name: str
    organization_installation_preference: Optional[Literal['auto_install', 'available', 'not_available', 'required']] = None
    organization_installation_preference_inherited: Optional[bool] = None
    owner: Owner
    reach: Optional[Literal['contained', 'privileged', 'remote']] = None
    served_version_id: str
    served_version_pinned: bool
    type: Literal['plugin']
    updated_at: datetime
