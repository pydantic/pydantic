
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_plugin_owner_user import BetaPluginOwnerUser
from .beta_plugin_owner_organization import BetaPluginOwnerOrganization
Owner: TypeAlias = Annotated[Union[BetaPluginOwnerOrganization, BetaPluginOwnerUser], UnionDiscriminator('type')]

class BetaPluginMarketplace(BaseModel):
    id: str
    created_at: datetime
    default_installation_preference: Optional[Literal['auto_install', 'available', 'not_available', 'required']] = None
    last_sync_ended_at: Optional[datetime] = None
    last_sync_read_sha: Optional[str] = None
    name: str
    owner: Owner
    source: Literal['directory', 'github', 'gitlab', 'manual', 'public_git']
    sync_status: Optional[Literal['failed_auth', 'failed_content', 'failed_limits', 'failed_transient', 'in_progress', 'success']] = None
    type: Literal['plugin_marketplace']
